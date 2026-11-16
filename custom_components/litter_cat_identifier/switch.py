"""Display preference: show or hide unidentified readings in the visits card."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_OFF, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import LitterConfigEntry
from .entity import LitterEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: LitterConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([ShowUnidentifiedSwitch(entry.runtime_data)])


class ShowUnidentifiedSwitch(LitterEntity, SwitchEntity, RestoreEntity):
    """Only affects how cards display the log; nothing is deleted."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:eye-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "show_unidentified")
        self._attr_is_on = True

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            self._attr_is_on = last.state != STATE_OFF

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._attr_is_on = False
        self.async_write_ha_state()
