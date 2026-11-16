"""Sensors: last visit, unidentified count, and per-cat weight / visits / last seen."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import LitterConfigEntry
from .const import UNIDENTIFIED
from .entity import LitterEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: LitterConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    c = entry.runtime_data
    entities: list[SensorEntity] = [LastVisitSensor(c), UnidentifiedTodaySensor(c)]
    for cat in c.cat_names:
        entities += [CatWeightSensor(c, cat), CatVisitsTodaySensor(c, cat), CatLastVisitSensor(c, cat)]
    async_add_entities(entities)


class LastVisitSensor(LitterEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_icon = "mdi:cat"
    _unrecorded_attributes = frozenset({"history"})

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "last_visit")
        self._attr_options = [*coordinator.cat_names, UNIDENTIFIED]

    @property
    def native_value(self) -> str | None:
        h = self.coordinator.history
        return h[0]["cat"] if h else None

    @property
    def entity_picture(self) -> str | None:
        return self.coordinator.picture(self.native_value)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        h = self.coordinator.history
        last = h[0] if h else {}
        return {
            "time": last.get("time"),
            "weight": last.get("weight"),
            "duration": last.get("duration"),
            "reason": last.get("reason"),
            "likely_cat": last.get("likely_cat"),
            "history": h,
        }


class UnidentifiedTodaySensor(LitterEntity, SensorEntity):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:help-circle-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "unidentified_today")

    @property
    def native_value(self) -> int:
        return self.coordinator.visits_today.get(UNIDENTIFIED, 0)


class CatWeightSensor(LitterEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfMass.KILOGRAMS
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator, cat: str) -> None:
        super().__init__(coordinator, "cat_weight", cat)

    @property
    def native_value(self) -> float:
        return self.coordinator.learned[self.cat]


class CatVisitsTodaySensor(LitterEntity, SensorEntity):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator, cat: str) -> None:
        super().__init__(coordinator, "cat_visits_today", cat)

    @property
    def native_value(self) -> int:
        return self.coordinator.visits_today.get(self.cat, 0)


class CatLastVisitSensor(LitterEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, cat: str) -> None:
        super().__init__(coordinator, "cat_last_visit", cat)

    @property
    def native_value(self) -> datetime | None:
        value = self.coordinator.last_visit.get(self.cat)
        return dt_util.parse_datetime(value) if value else None
