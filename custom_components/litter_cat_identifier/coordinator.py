"""Visit detection, cat identification, notifications and persistent state."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_NAME,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er, issue_registry as ir
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_change,
    async_track_time_interval,
)
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ALERT_HOURS,
    CONF_CAT_NAME,
    CONF_CAT_OPTIONS,
    CONF_CAT_WEIGHT,
    CONF_CATS,
    CONF_COLOR,
    CONF_DURATION_ENTITY,
    CONF_MIN_WEIGHT,
    CONF_NOTIFY_TARGETS,
    CONF_NOTIFY_HEALTH,
    CONF_NOTIFY_UNIDENTIFIED,
    CONF_NOTIFY_VISIT,
    CONF_RECORD_UNIDENTIFIED,
    CONF_PICTURE,
    CONF_SMOOTHING,
    CONF_TOLERANCE,
    CONF_VISIT_ENTITY,
    CONF_WEIGHT_ENTITY,
    COUNTER_DELAY,
    DEFAULT_MIN_WEIGHT,
    DEFAULT_SMOOTHING,
    DEFAULT_TOLERANCE,
    DOMAIN,
    STORED_HISTORY,
    INACTIVITY_CHECK,
    LEARN_SAMPLES,
    PARTIAL_WINDOW,
    REASON_PARTIAL,
    RECALIBRATE_SAMPLES,
    STORAGE_VERSION,
    UNIDENTIFIED,
    WEIGHT_DEBOUNCE,
    WEIGHT_BEFORE_COUNTER,
    WEIGHT_FRESHNESS,
    WEIGHT_SETTLE,
    WEIGHT_WAIT,
)
from . import health
from .logic import classify_unidentified, half_inside, identify, learn, median, parse_float, to_kg
from .messages import text
from .pictures import REFRESH_EVERY, picture_url

_LOGGER = logging.getLogger(__name__)

UAHPET = "uahpet"
BUSY_STATES = ("cleaning", "clearing", "leveling")
BUSY_WINDOW = 120  # s: readings right after the litter box moved the litter are not a cat
LIVE_SCALE_DROPS = 3  # weight sensor fell back to ~0 this many times: it is a live scale


def signal_update(entry_id: str) -> str:
    return f"{DOMAIN}_update_{entry_id}"


def signal_visit(entry_id: str) -> str:
    return f"{DOMAIN}_visit_{entry_id}"


class LitterCoordinator:
    """Watches the litter box sensors and keeps per-cat stats."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.name: str = entry.data[CONF_NAME]
        self.cat_names: list[str] = [c[CONF_CAT_NAME] for c in entry.data[CONF_CATS]]
        self._initial = {c[CONF_CAT_NAME]: float(c[CONF_CAT_WEIGHT]) for c in entry.data[CONF_CATS]}

        self.weight_entity: str = entry.data[CONF_WEIGHT_ENTITY]
        self.visit_entity: str | None = entry.data.get(CONF_VISIT_ENTITY)
        self.duration_entity: str | None = entry.data.get(CONF_DURATION_ENTITY)

        opts = entry.options
        self.tolerance = float(opts.get(CONF_TOLERANCE, DEFAULT_TOLERANCE))
        self.smoothing = float(opts.get(CONF_SMOOTHING, DEFAULT_SMOOTHING))
        self.min_weight = float(opts.get(CONF_MIN_WEIGHT, DEFAULT_MIN_WEIGHT))
        self.notify_targets: list[str] = list(opts.get(CONF_NOTIFY_TARGETS, []))
        self.notify_unidentified: bool = bool(opts.get(CONF_NOTIFY_UNIDENTIFIED, False))
        self.notify_health: bool = bool(opts.get(CONF_NOTIFY_HEALTH, True))
        self.record_unidentified: bool = bool(opts.get(CONF_RECORD_UNIDENTIFIED, True))
        cat_opts = opts.get(CONF_CAT_OPTIONS, {})
        self.cat_settings: dict[str, dict[str, Any]] = {
            n: {
                CONF_PICTURE: cat_opts.get(n, {}).get(CONF_PICTURE) or None,
                CONF_NOTIFY_VISIT: bool(cat_opts.get(n, {}).get(CONF_NOTIFY_VISIT, False)),
                CONF_ALERT_HOURS: float(cat_opts.get(n, {}).get(CONF_ALERT_HOURS, 0) or 0),
                CONF_COLOR: cat_opts.get(n, {}).get(CONF_COLOR),
            }
            for n in self.cat_names
        }

        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
        self.learned: dict[str, float] = {}
        self.visits_today: dict[str, int] = {}
        self.last_visit: dict[str, str | None] = {}
        self.alerted: dict[str, bool] = {}
        self.history: list[dict[str, Any]] = []
        self._day: str = ""
        self.daily: dict[str, dict[str, int]] = {}  # day -> visits per cat (health baseline)
        self.weights: dict[str, dict[str, float]] = {}  # day -> learned weight per cat
        self.health: dict[str, dict[str, Any]] = {}  # cat -> active reason -> detail
        # UAHPET litter box entities next to the visit / weight source (translation_key -> entity_id)
        self.device_entities: dict[str, str] = {}
        self._busy_at = None
        self._weight_drops = 0
        self._weight_above = False

        self._last_weight: float | None = None
        self._last_weight_at = None
        self._pending_weight: float | None = None
        self._cancel_timer: Callable[[], None] | None = None
        self._cancel_wait: Callable[[], None] | None = None  # counter ticked, waiting for the weight
        self._unsubs: list[Callable[[], None]] = []

    def color(self, cat: str | None) -> str | None:
        """Cat colour as #rrggbb (charts, icons), if one was picked."""
        rgb = self.cat_settings.get(cat, {}).get(CONF_COLOR) if cat else None
        return "#{:02x}{:02x}{:02x}".format(*rgb) if rgb and len(rgb) == 3 else None

    def picture(self, cat: str | None) -> str | None:
        """Photo URL for entities and notifications (our own photos come signed)."""
        return picture_url(self.hass, self.cat_settings.get(cat, {}).get(CONF_PICTURE)) if cat else None

    # ---------- persistence ----------

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        stored = data.get("learned", {})
        self.learned = {n: float(stored.get(n, self._initial[n])) for n in self.cat_names}
        self.history = data.get("history", [])[:STORED_HISTORY]
        self.last_visit = {n: data.get("last_visit", {}).get(n) for n in self.cat_names}
        self.alerted = {n: bool(data.get("alerted", {}).get(n, False)) for n in self.cat_names}
        self._day = data.get("day", "")
        self.daily = data.get("daily", {})
        self.weights = data.get("weights", {})
        self.health = {n: dict(data.get("health", {}).get(n, {})) for n in self.cat_names}
        counts = data.get("visits_today", {})
        self.visits_today = {n: int(counts.get(n, 0)) for n in [*self.cat_names, UNIDENTIFIED]}
        if self._day != self._today():
            self._reset_day()

    def _save(self) -> None:
        self._store.async_delay_save(self._as_dict, 5)

    def _as_dict(self) -> dict[str, Any]:
        return {
            "learned": self.learned,
            "visits_today": self.visits_today,
            "last_visit": self.last_visit,
            "alerted": self.alerted,
            "history": self.history,
            "day": self._day,
            "daily": self.daily,
            "weights": self.weights,
            "health": self.health,
        }

    # ---------- lifecycle ----------

    @callback
    def async_start(self) -> None:
        self.device_entities = self._find_device_entities()
        if status := self.device_entities.get("work_status"):
            self._unsubs.append(async_track_state_change_event(self.hass, [status], self._on_device_status))
        ir.async_delete_issue(self.hass, DOMAIN, self._live_scale_issue)
        self._check_weight_loss()
        self._unsubs.append(
            async_track_state_change_event(self.hass, [self.weight_entity], self._on_weight)
        )
        if self.visit_entity:
            self._unsubs.append(
                async_track_state_change_event(self.hass, [self.visit_entity], self._on_counter)
            )
        self._unsubs.append(
            async_track_time_change(self.hass, self._on_midnight, hour=0, minute=0, second=0)
        )
        if any(s[CONF_PICTURE] for s in self.cat_settings.values()):
            # signed photo URLs expire: let entities pick up a fresh one in time
            self._unsubs.append(
                async_track_time_interval(self.hass, self._refresh_pictures, REFRESH_EVERY)
            )
        if any(s[CONF_ALERT_HOURS] for s in self.cat_settings.values()):
            self._unsubs.append(
                async_track_time_interval(
                    self.hass, self._check_inactivity, timedelta(seconds=INACTIVITY_CHECK)
                )
            )

    async def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        if self._cancel_timer:
            self._cancel_timer()
            self._cancel_timer = None
        if self._cancel_wait:
            self._cancel_wait()
            self._cancel_wait = None
        await self._store.async_save(self._as_dict())

    # ---------- helpers ----------

    @staticmethod
    def _today() -> str:
        return dt_util.now().date().isoformat()

    def _reset_day(self) -> None:
        if self._day and self.visits_today:
            # keep each day's counts and weights: the baseline for health alerts
            self.daily[self._day] = {n: self.visits_today.get(n, 0) for n in self.cat_names}
            self.weights[self._day] = dict(self.learned)
            today = dt_util.now().date()
            health.trim(self.daily, today)
            health.trim(self.weights, today)
        self._day = self._today()
        self.visits_today = {n: 0 for n in [*self.cat_names, UNIDENTIFIED]}
        # daily signals end with the day; weight loss is re-evaluated
        for cat in self.cat_names:
            self.health.setdefault(cat, {}).pop("frequent_visits", None)
            self.health[cat].pop("long_visit", None)
        self._check_weight_loss()

    # ---------- litter box context (UAHPET) ----------

    def _find_device_entities(self) -> dict[str, str]:
        """UAHPET entities on the same device as the visit / weight source."""
        reg = er.async_get(self.hass)
        for source in (self.visit_entity, self.weight_entity):
            entry = reg.async_get(source) if source else None
            if entry and entry.platform == UAHPET and entry.device_id:
                return {
                    e.translation_key: e.entity_id
                    for e in er.async_entries_for_device(reg, entry.device_id)
                    if e.platform == UAHPET and e.translation_key
                }
        return {}

    @callback
    def _on_device_status(self, event: Event[EventStateChangedData]) -> None:
        new = event.data["new_state"]
        if new is not None and new.state in BUSY_STATES:
            self._busy_at = dt_util.utcnow()

    def _device_reason(self) -> str | None:
        """Why an unidentified reading is not a cat, from the litter box's own state."""
        ents = self.device_entities
        if not ents:
            return None
        stagnant = ents.get("stagnant") and self.hass.states.get(ents["stagnant"])
        if stagnant and stagnant.state == "on":
            return "stayed_too_long"
        status = ents.get("work_status") and self.hass.states.get(ents["work_status"])
        if status and status.state in BUSY_STATES:
            return "device_busy"
        if self._busy_at and (dt_util.utcnow() - self._busy_at).total_seconds() <= BUSY_WINDOW:
            return "device_busy"
        return None

    # ---------- weight source check ----------

    @property
    def _live_scale_issue(self) -> str:
        return f"live_scale_{self.entry.entry_id}"

    def _check_live_scale(self, state) -> None:
        """A weight sensor that keeps falling back to ~0 is a live scale: visits get partial weights."""
        if self.visit_entity and self.visit_entity.startswith("event."):
            return  # the event carries the weight; the sensor is only a fallback
        value = parse_float(state.state) if state else None
        if value is None:
            return
        above = to_kg(value, state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)) >= self.min_weight
        if self._weight_above and not above:
            self._weight_drops += 1
            if self._weight_drops == LIVE_SCALE_DROPS:
                suggestion = self.device_entities.get("visit") or self._find_device_entities().get("visit")
                ir.async_create_issue(
                    self.hass, DOMAIN, self._live_scale_issue, is_fixable=False, is_persistent=False,
                    severity=ir.IssueSeverity.WARNING, translation_key="live_scale",
                    translation_placeholders={"name": self.name, "entity": self.weight_entity, "suggestion": suggestion or "-"},
                )
        self._weight_above = above

    # ---------- health ----------

    def _check_weight_loss(self) -> None:
        today = dt_util.now().date()
        changed = False
        for cat in self.cat_names:
            snapshots = {d: w.get(cat) for d, w in self.weights.items() if w.get(cat)}
            pct = health.weight_loss(self.learned.get(cat), snapshots, today)
            active = self.health.setdefault(cat, {})
            if pct is not None and "weight_loss" not in active:
                active["weight_loss"] = pct
                changed = True
                self._notify_health(cat, "weight_loss", pct=pct)
            elif pct is None and "weight_loss" in active:
                del active["weight_loss"]
                changed = True
        if changed:
            self._notify_entities()

    def _check_visit_health(self, cat: str, duration: float | None) -> None:
        active = self.health.setdefault(cat, {})
        past_counts = [d.get(cat, 0) for d in self.daily.values()]
        if "frequent_visits" not in active and health.frequent_visits(self.visits_today.get(cat, 0), past_counts):
            active["frequent_visits"] = self.visits_today.get(cat, 0)
            self._notify_health(cat, "frequent_visits", count=active["frequent_visits"])
        past_durations = [v["duration"] for v in self.history[1:200] if v["cat"] == cat and v.get("duration")]
        if "long_visit" not in active and health.long_visit(duration, past_durations):
            active["long_visit"] = round(duration)
            self._notify_health(cat, "long_visit", seconds=round(duration))

    def _notify_health(self, cat: str, reason: str, **kwargs: Any) -> None:
        if self.notify_health:
            self._send(text(self.hass.config.language, f"health_{reason}", cat=cat, **kwargs), self.picture(cat))

    def _read_kg(self, state) -> float | None:
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return None
        value = parse_float(state.state)
        if value is None:
            return None
        kg = to_kg(value, state.attributes.get(ATTR_UNIT_OF_MEASUREMENT))
        return kg if kg >= self.min_weight else None

    def _read_duration(self) -> float | None:
        if not self.duration_entity:
            return None
        state = self.hass.states.get(self.duration_entity)
        return parse_float(state.state) if state else None

    @callback
    def _refresh_pictures(self, _now) -> None:
        self._notify_entities()

    def _notify_entities(self) -> None:
        async_dispatcher_send(self.hass, signal_update(self.entry.entry_id))

    # ---------- notifications ----------

    def _send(self, message: str, picture: str | None = None) -> None:
        if not self.notify_targets:
            return
        self.entry.async_create_background_task(
            self.hass, self._async_send(message, picture), f"{DOMAIN}_notify"
        )

    async def _async_send(self, message: str, picture: str | None) -> None:
        for target in self.notify_targets:
            domain, _, service = target.partition(".")
            if not self.hass.services.has_service(domain, service):
                _LOGGER.warning("Notify service %s not found", target)
                continue
            data: dict[str, Any] = {"title": f"🐈 {self.name}", "message": message}
            if picture and service.startswith("mobile_app_"):
                data["data"] = {"image": picture}
            try:
                await self.hass.services.async_call(domain, service, data, blocking=True)
            except Exception:  # noqa: BLE001 - one bad target must not stop the others
                _LOGGER.exception("Failed to notify %s", target)

    @callback
    def _check_inactivity(self, now=None) -> None:
        now = now or dt_util.now()
        changed = False
        for cat, settings in self.cat_settings.items():
            hours = settings[CONF_ALERT_HOURS]
            last = self.last_visit.get(cat)
            if not hours or not last or self.alerted.get(cat):
                continue
            last_dt = dt_util.parse_datetime(last)
            if last_dt and now - last_dt > timedelta(hours=hours):
                self.alerted[cat] = True
                changed = True
                self._send(
                    text(self.hass.config.language, "inactive", cat=cat, hours=f"{hours:g}"),
                    self.picture(cat),
                )
        if changed:
            self._save()

    # ---------- event handlers ----------

    @callback
    def _on_midnight(self, _now) -> None:
        self._reset_day()
        self._save()
        self._notify_entities()

    @callback
    def _on_weight(self, event: Event[EventStateChangedData]) -> None:
        self._check_live_scale(event.data["new_state"])
        kg = self._read_kg(event.data["new_state"])
        if kg is None:
            return
        self._last_weight = kg
        self._last_weight_at = dt_util.utcnow()
        if self.visit_entity:
            # Counter mode: the counter decides when a visit happened. If it ticked before
            # the weight arrived, this is the visit's weight: record it (shortly, for the duration).
            if self._cancel_wait:
                self._cancel_wait()
                self._cancel_wait = async_call_later(self.hass, WEIGHT_SETTLE, self._flush_counter)
            return
        self._pending_weight = kg
        if self._cancel_timer:
            self._cancel_timer()
        self._cancel_timer = async_call_later(self.hass, WEIGHT_DEBOUNCE, self._flush_weight)

    @callback
    def _flush_weight(self, _now) -> None:
        self._cancel_timer = None
        if self._pending_weight is not None:
            self._record(self._pending_weight)
            self._pending_weight = None

    @callback
    def _on_counter(self, event: Event[EventStateChangedData]) -> None:
        old, new = event.data["old_state"], event.data["new_state"]
        if old is None or new is None:
            return
        if new.domain == "event":
            self._on_visit_event(old, new)
            return
        old_v, new_v = parse_float(old.state), parse_float(new.state)
        if old_v is None or new_v is None or new_v <= old_v:
            return  # daily reset or unavailable, not a visit
        if self._cancel_wait:  # previous visit never got its weight: record it now
            self._flush_counter(None)
        fresh = self._last_weight_at and (dt_util.utcnow() - self._last_weight_at).total_seconds() <= WEIGHT_BEFORE_COUNTER
        if fresh:
            async_call_later(self.hass, COUNTER_DELAY, self._flush_counter)
        else:
            # Some litter boxes send the visit weight after the counter: wait for it.
            self._cancel_wait = async_call_later(self.hass, WEIGHT_WAIT, self._flush_counter)

    @callback
    def _on_visit_event(self, old, new) -> None:
        """A visit event entity (e.g. UAHPET) carries the visit's weight and duration together."""
        if old.state == STATE_UNAVAILABLE or new.state in (STATE_UNKNOWN, STATE_UNAVAILABLE) or new.state == old.state:
            return  # restored after a restart / reload, not a new visit
        attrs = new.attributes
        kg = parse_float(attrs.get("weight"))
        kg = to_kg(kg, attrs.get(ATTR_UNIT_OF_MEASUREMENT) or "kg") if kg is not None else None
        if kg is None or kg < self.min_weight:
            kg = self._read_kg(self.hass.states.get(self.weight_entity))
        self._record(kg, parse_float(attrs.get("duration")))

    @callback
    def _flush_counter(self, _now) -> None:
        if self._cancel_wait:
            self._cancel_wait()
            self._cancel_wait = None
        kg = self._read_kg(self.hass.states.get(self.weight_entity))
        if kg is None and self._last_weight_at is not None:
            age = (dt_util.utcnow() - self._last_weight_at).total_seconds()
            if age <= WEIGHT_FRESHNESS:
                kg = self._last_weight
        self._record(kg)

    # ---------- core ----------

    def _record(self, kg: float | None, duration: float | None = None) -> None:
        if self._day != self._today():
            self._reset_day()

        now_dt = dt_util.now()
        now = now_dt.isoformat()
        prev = self.history[0] if self.history else None
        since = None
        if prev and (prev_dt := dt_util.parse_datetime(prev["time"])):
            since = (now_dt - prev_dt).total_seconds()
        prev_cat = prev["cat"] if prev and prev["cat"] in self.cat_names else None

        cat = identify(kg, self.learned, self.tolerance) if kg is not None else None
        partial_of = None
        if cat is not None and prev_cat not in (None, cat):
            partial_of = half_inside(kg, self.learned[cat], self.tolerance, prev, since, PARTIAL_WINDOW)
            if partial_of:
                cat = None  # lighter than the cat, right after a heavier cat's visit
        if cat is None and not self.record_unidentified:
            _LOGGER.debug("Ignoring unidentified reading %s (recording disabled)", kg)
            return
        if cat is not None and kg is not None:
            recent = [v["weight"] for v in self.history if v["cat"] == cat and v.get("weight") is not None]
            typical = median([kg, *recent[: LEARN_SAMPLES - 1]])
            self.learned[cat] = round(learn(self.learned[cat], typical, self.smoothing), 3)

        key = cat or UNIDENTIFIED

        reason = likely = None
        if partial_of:
            reason, likely = REASON_PARTIAL, partial_of
        elif not cat:
            reason, likely = classify_unidentified(kg, since, prev_cat, PARTIAL_WINDOW)
            if device_reason := self._device_reason():
                reason, likely = device_reason, None
        self.visits_today[key] = self.visits_today.get(key, 0) + 1
        if cat:
            self.last_visit[cat] = now
            self.alerted[cat] = False

        visit = {
            "time": now,
            "cat": key,
            "weight": round(kg, 2) if kg is not None else None,
            "duration": duration if duration is not None else self._read_duration(),
        }
        if reason:
            visit["reason"] = reason
            visit["likely_cat"] = likely
        self.history.insert(0, visit)
        del self.history[STORED_HISTORY:]
        if cat:
            self._check_visit_health(cat, visit["duration"])

        _LOGGER.debug("Visit recorded: %s", visit)
        self._save()
        async_dispatcher_send(self.hass, signal_visit(self.entry.entry_id), visit)
        self._notify_entities()

        lang = self.hass.config.language
        if cat and self.cat_settings[cat][CONF_NOTIFY_VISIT]:
            self._send(text(lang, "visit", cat=cat, weight=visit["weight"]), self.picture(cat))
        elif not cat and self.notify_unidentified:
            self._send(text(lang, f"unidentified_{reason}", weight=visit["weight"], cat=likely or ""))

    def reassign_last(self, cat: str) -> None:
        """Fix the most recent visit when identification got it wrong."""
        if cat not in self.cat_names:
            raise ValueError(f"Unknown cat: {cat}")
        if not self.history:
            raise ValueError("No visits recorded yet")

        visit = self.history[0]
        old = visit["cat"]
        if old == cat:
            return

        if visit["time"][:10] == self._day:
            self.visits_today[old] = max(0, self.visits_today.get(old, 0) - 1)
            self.visits_today[cat] = self.visits_today.get(cat, 0) + 1

        visit["cat"] = cat
        visit.pop("reason", None)
        visit.pop("likely_cat", None)
        self.last_visit[cat] = visit["time"]
        self.alerted[cat] = False
        if old in self.cat_names:
            self.last_visit[old] = next(
                (v["time"] for v in self.history if v["cat"] == old), None
            )
        if visit["weight"] is not None:
            self.learned[cat] = round(learn(self.learned[cat], visit["weight"], self.smoothing), 3)

        self._save()
        self._notify_entities()

    def recalibrate(
        self, cat: str, weight: float | None = None, samples: int = RECALIBRATE_SAMPLES
    ) -> float:
        """Reset a cat's learned weight: given value, or median of its latest readings."""
        if cat not in self.cat_names:
            raise ValueError(f"Unknown cat: {cat}")
        if weight is None:
            readings = [v["weight"] for v in self.history if v["cat"] == cat and v["weight"] is not None]
            if not readings:
                raise ValueError(f"No recent weighed visits for {cat}")
            weight = median(readings[: max(1, int(samples))])
        self.learned[cat] = round(float(weight), 3)
        self._save()
        self._notify_entities()
        return self.learned[cat]

    def clear_unidentified(self) -> int:
        """Drop unidentified readings from the log and reset today's count."""
        before = len(self.history)
        self.history = [v for v in self.history if v["cat"] != UNIDENTIFIED]
        self.visits_today[UNIDENTIFIED] = 0
        self._save()
        self._notify_entities()
        return before - len(self.history)
