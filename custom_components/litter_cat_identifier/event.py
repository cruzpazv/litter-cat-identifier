"""Event entity: fires once per visit, event_type = cat name (or 'unidentified')."""

from __future__ import annotations

from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LitterConfigEntry
from .const import UNIDENTIFIED
from .coordinator import signal_visit
from .entity import LitterEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: LitterConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([VisitEvent(entry.runtime_data)])


class VisitEvent(LitterEntity, EventEntity):
    _attr_icon = "mdi:paw"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "visit")
        self._attr_event_types = [*coordinator.cat_names, UNIDENTIFIED]

    async def async_added_to_hass(self) -> None:
        # no update-signal subscription: the event state only changes on visits
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, signal_visit(self.coordinator.entry.entry_id), self._on_visit
            )
        )

    @callback
    def _on_visit(self, visit: dict[str, Any]) -> None:
        self._trigger_event(
            visit["cat"], {"weight": visit["weight"], "duration": visit["duration"]}
        )
        self.async_write_ha_state()
