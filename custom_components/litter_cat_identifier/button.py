"""Per-cat button: reset the learned weight to the median of the latest readings."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LitterConfigEntry
from .entity import LitterEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: LitterConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    c = entry.runtime_data
    async_add_entities([ClearUnidentifiedButton(c), *(RecalibrateButton(c, cat) for cat in c.cat_names)])


class RecalibrateButton(LitterEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:scale-balance"

    def __init__(self, coordinator, cat: str) -> None:
        super().__init__(coordinator, "recalibrate", cat)

    @property
    def entity_picture(self) -> str | None:
        return None  # keep the scale icon on the button

    async def async_press(self) -> None:
        try:
            self.coordinator.recalibrate(self.cat)
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err


class ClearUnidentifiedButton(LitterEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:broom"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "clear_unidentified")

    async def async_press(self) -> None:
        self.coordinator.clear_unidentified()
