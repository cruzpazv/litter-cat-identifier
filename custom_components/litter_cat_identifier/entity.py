"""Base entity."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.util import slugify

from .const import DOMAIN
from .coordinator import LitterCoordinator, signal_update


class LitterEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: LitterCoordinator, key: str, cat: str | None = None) -> None:
        self.coordinator = coordinator
        self.cat = cat
        entry_id = coordinator.entry.entry_id
        self._attr_unique_id = f"{entry_id}_{key}" + (f"_{slugify(cat)}" if cat else "")
        self._attr_translation_key = key
        if cat:
            self._attr_translation_placeholders = {"cat": cat}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=coordinator.name,
            manufacturer="Litter Cat Identifier",
            model="Weight-based cat identification",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, signal_update(self.coordinator.entry.entry_id), self.async_write_ha_state
            )
        )
