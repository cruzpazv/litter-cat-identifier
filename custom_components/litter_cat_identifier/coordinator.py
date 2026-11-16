"""Visit detection, cat identification and persistent state."""

from __future__ import annotations

from collections.abc import Callable
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
)
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CAT_NAME,
    CONF_CAT_WEIGHT,
    CONF_CATS,
    CONF_DURATION_ENTITY,
    CONF_MIN_WEIGHT,
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
    STORAGE_VERSION,
    UNIDENTIFIED,
    WEIGHT_DEBOUNCE,
    WEIGHT_FRESHNESS,
)
from .logic import identify, learn, parse_float, to_kg

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

        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
        self.learned: dict[str, float] = {}
        self.visits_today: dict[str, int] = {}
        self.last_visit: dict[str, str | None] = {}
        self.history: list[dict[str, Any]] = []
        self._day: str = ""

        self._last_weight: float | None = None
        self._last_weight_at = None
        self._pending_weight: float | None = None
        self._cancel_timer: Callable[[], None] | None = None
        self._unsubs: list[Callable[[], None]] = []

    # ---------- persistence ----------

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        stored = data.get("learned", {})
        self.learned = {n: float(stored.get(n, self._initial[n])) for n in self.cat_names}
        self.history = data.get("history", [])[:HISTORY_SIZE]
        self.last_visit = {n: data.get("last_visit", {}).get(n) for n in self.cat_names}
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

    def _notify(self) -> None:
        async_dispatcher_send(self.hass, signal_update(self.entry.entry_id))

    # ---------- event handlers ----------

    @callback
    def _on_midnight(self, _now) -> None:
        self._reset_day()
        self._save()
        self._notify()

    @callback
    def _on_weight(self, event: Event[EventStateChangedData]) -> None:
        kg = self._read_kg(event.data["new_state"])
        if kg is None:
            return
        self._last_weight = kg
        self._last_weight_at = dt_util.utcnow()
        if self.visit_entity:
            return  # counter mode: the counter decides when a visit happened
        # weight-only mode: wait until the reading settles
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
        # give the weight sensor a moment to report
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
        now = dt_util.now().isoformat()
        self.visits_today[key] = self.visits_today.get(key, 0) + 1
        if cat:
            self.last_visit[cat] = now

        visit = {
            "time": now,
            "cat": key,
            "weight": round(kg, 2) if kg is not None else None,
            "duration": self._read_duration(),
        }
        self.history.insert(0, visit)
        del self.history[HISTORY_SIZE:]

        _LOGGER.debug("Visit recorded: %s", visit)
        self._save()
        async_dispatcher_send(self.hass, signal_visit(self.entry.entry_id), visit)
        self._notify()

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
        self.last_visit[cat] = visit["time"]
        if old in self.cat_names:
            self.last_visit[old] = next(
                (v["time"] for v in self.history if v["cat"] == old), None
            )
        if visit["weight"] is not None:
            self.learned[cat] = round(learn(self.learned[cat], visit["weight"], self.smoothing), 3)

        self._save()
        self._notify()
