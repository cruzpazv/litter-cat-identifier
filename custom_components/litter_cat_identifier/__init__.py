"""Litter Cat Identifier: tells cats apart by weight on an automatic litter box."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import ATTR_CAT, ATTR_CONFIG_ENTRY_ID, DOMAIN, SERVICE_REASSIGN
from .coordinator import LitterCoordinator

PLATFORMS = [Platform.SENSOR, Platform.EVENT]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type LitterConfigEntry = ConfigEntry[LitterCoordinator]

REASSIGN_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CAT): cv.string,
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    async def _reassign(call: ServiceCall) -> None:
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
        try:
            loaded[0].runtime_data.reassign_last(call.data[ATTR_CAT])
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err

    hass.services.async_register(DOMAIN, SERVICE_REASSIGN, _reassign, schema=REASSIGN_SCHEMA)
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
