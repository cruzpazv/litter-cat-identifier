"""Per-cat health binary sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import LitterEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    async_add_entities(CatHealthSensor(c, cat) for cat in c.cat_names)


class CatHealthSensor(LitterEntity, BinarySensorEntity):
    """On when one of the cat's health signals is active; `reasons` says which."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:heart-pulse"

    def __init__(self, coordinator, cat: str) -> None:
        super().__init__(coordinator, "cat_health", cat)

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.health.get(self.cat))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        active = self.coordinator.health.get(self.cat, {})
        return {"cat": self.cat, "reasons": list(active), **{k: v for k, v in active.items()}}
