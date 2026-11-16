"""Litter Cat Identifier: tells cats apart by weight on an automatic litter box."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTR_CAT,
    ATTR_CONFIG_ENTRY_ID,
    ATTR_SAMPLES,
    ATTR_WEIGHT,
    CONF_CAT_OPTIONS,
    CONF_PICTURE,
    DOMAIN,
    RECALIBRATE_SAMPLES,
    SERVICE_REASSIGN,
    SERVICE_CLEAR_UNIDENTIFIED,
    SERVICE_RECALIBRATE,
)
from .coordinator import LitterCoordinator
from .frontend import async_register_cards
from .pictures import async_delete_pictures, async_register_static_path

PLATFORMS = [Platform.BUTTON, Platform.EVENT, Platform.SENSOR, Platform.SWITCH]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type LitterConfigEntry = ConfigEntry[LitterCoordinator]

REASSIGN_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CAT): cv.string,
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    }
)
CLEAR_SCHEMA = vol.Schema({vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string})
RECALIBRATE_SCHEMA = REASSIGN_SCHEMA.extend(
    {
        vol.Optional(ATTR_WEIGHT): vol.All(vol.Coerce(float), vol.Range(min=0.3, max=20)),
        vol.Optional(ATTR_SAMPLES, default=RECALIBRATE_SAMPLES): vol.All(vol.Coerce(int), vol.Range(min=1, max=20)),
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    def _coordinator(call: ServiceCall) -> LitterCoordinator:
        loaded = [
            e for e in hass.config_entries.async_entries(DOMAIN)
            if e.state is ConfigEntryState.LOADED
        ]
        entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
        if entry_id:
            loaded = [e for e in loaded if e.entry_id == entry_id]
        if len(loaded) != 1:
            raise ServiceValidationError(
                "Specify config_entry_id when more than one litter box is set up"
                if len(loaded) > 1 else "Litter box not found"
            )
        return loaded[0].runtime_data

    async def _reassign(call: ServiceCall) -> None:
        try:
            _coordinator(call).reassign_last(call.data[ATTR_CAT])
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err

    async def _recalibrate(call: ServiceCall) -> None:
        try:
            _coordinator(call).recalibrate(
                call.data[ATTR_CAT], call.data.get(ATTR_WEIGHT), call.data[ATTR_SAMPLES]
            )
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err

    hass.services.async_register(DOMAIN, SERVICE_REASSIGN, _reassign, schema=REASSIGN_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_RECALIBRATE, _recalibrate, schema=RECALIBRATE_SCHEMA)

    async def _clear(call: ServiceCall) -> None:
        _coordinator(call).clear_unidentified()

    hass.services.async_register(DOMAIN, SERVICE_CLEAR_UNIDENTIFIED, _clear, schema=CLEAR_SCHEMA)
    await async_register_static_path(hass)
    await async_register_cards(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: LitterConfigEntry) -> bool:
    coordinator = LitterCoordinator(hass, entry)
    await coordinator.async_load()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    coordinator.async_start()
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LitterConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_stop()
    return unloaded


async def _async_reload(hass: HomeAssistant, entry: LitterConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(hass: HomeAssistant, entry: LitterConfigEntry) -> None:
    """Delete the photos this entry stored."""
    pictures = [o.get(CONF_PICTURE) for o in entry.options.get(CONF_CAT_OPTIONS, {}).values()]
    await async_delete_pictures(hass, pictures)
