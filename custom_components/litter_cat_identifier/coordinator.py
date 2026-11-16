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
    CONF_DURATION_ENTITY,
    CONF_MIN_WEIGHT,
    CONF_NOTIFY_TARGETS,
    CONF_NOTIFY_UNIDENTIFIED,
    CONF_NOTIFY_VISIT,
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
    HISTORY_SIZE,
    INACTIVITY_CHECK,
    PARTIAL_WINDOW,
    RECALIBRATE_SAMPLES,
    STORAGE_VERSION,
    UNIDENTIFIED,
    WEIGHT_DEBOUNCE,
    WEIGHT_FRESHNESS,
)
from .logic import classify_unidentified, identify, learn, median, parse_float, to_kg
from .messages import text

_LOGGER = logging.getLogger(__name__)


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
        cat_opts = opts.get(CONF_CAT_OPTIONS, {})
        self.cat_settings: dict[str, dict[str, Any]] = {
            n: {
                CONF_PICTURE: cat_opts.get(n, {}).get(CONF_PICTURE) or None,
                CONF_NOTIFY_VISIT: bool(cat_opts.get(n, {}).get(CONF_NOTIFY_VISIT, False)),
                CONF_ALERT_HOURS: float(cat_opts.get(n, {}).get(CONF_ALERT_HOURS, 0) or 0),
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

        self._last_weight: float | None = None
        self._last_weight_at = None
        self._pending_weight: float | None = None
        self._cancel_timer: Callable[[], None] | None = None
        self._unsubs: list[Callable[[], None]] = []

    def picture(self, cat: str | None) -> str | None:
        return self.cat_settings.get(cat, {}).get(CONF_PICTURE) if cat else None

    # ---------- persistence ----------

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        stored = data.get("learned", {})
        self.learned = {n: float(stored.get(n, self._initial[n])) for n in self.cat_names}
        self.history = data.get("history", [])[:HISTORY_SIZE]
        self.last_visit = {n: data.get("last_visit", {}).get(n) for n in self.cat_names}
        self.alerted = {n: bool(data.get("alerted", {}).get(n, False)) for n in self.cat_names}
        self._day = data.get("day", "")
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
        }

    # ---------- lifecycle ----------

    @callback
    def async_start(self) -> None:
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
        await self._store.async_save(self._as_dict())

    # ---------- helpers ----------

    @staticmethod
    def _today() -> str:
        return dt_util.now().date().isoformat()

    def _reset_day(self) -> None:
        self._day = self._today()
        self.visits_today = {n: 0 for n in [*self.cat_names, UNIDENTIFIED]}

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
        kg = self._read_kg(event.data["new_state"])
        if kg is None:
            return
        self._last_weight = kg
        self._last_weight_at = dt_util.utcnow()
        if self.visit_entity:
            return  # counter mode: the counter decides when a visit happened
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
        old_v, new_v = parse_float(old.state), parse_float(new.state)
        if old_v is None or new_v is None or new_v <= old_v:
            return  # daily reset or unavailable, not a visit
        async_call_later(self.hass, COUNTER_DELAY, self._flush_counter)

    @callback
    def _flush_counter(self, _now) -> None:
        kg = self._read_kg(self.hass.states.get(self.weight_entity))
        if kg is None and self._last_weight_at is not None:
            age = (dt_util.utcnow() - self._last_weight_at).total_seconds()
            if age <= WEIGHT_FRESHNESS:
                kg = self._last_weight
        self._record(kg)

    # ---------- core ----------

    def _record(self, kg: float | None) -> None:
        if self._day != self._today():
            self._reset_day()

        cat = identify(kg, self.learned, self.tolerance) if kg is not None else None
        if cat is not None and kg is not None:
            self.learned[cat] = round(learn(self.learned[cat], kg, self.smoothing), 3)

        key = cat or UNIDENTIFIED
        now_dt = dt_util.now()
        now = now_dt.isoformat()

        reason = likely = None
        if not cat:
            prev = self.history[0] if self.history else None
            since = None
            if prev and (prev_dt := dt_util.parse_datetime(prev["time"])):
                since = (now_dt - prev_dt).total_seconds()
            prev_cat = prev["cat"] if prev and prev["cat"] in self.cat_names else None
            reason, likely = classify_unidentified(kg, since, prev_cat, PARTIAL_WINDOW)
        self.visits_today[key] = self.visits_today.get(key, 0) + 1
        if cat:
            self.last_visit[cat] = now
            self.alerted[cat] = False

        visit = {
            "time": now,
            "cat": key,
            "weight": round(kg, 2) if kg is not None else None,
            "duration": self._read_duration(),
        }
        if reason:
            visit["reason"] = reason
            visit["likely_cat"] = likely
        self.history.insert(0, visit)
        del self.history[HISTORY_SIZE:]

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
