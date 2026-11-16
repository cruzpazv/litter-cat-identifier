"""Config and options flow."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
)

from .const import (
    CONF_ADD_ANOTHER,
    CONF_CAT_NAME,
    CONF_CAT_WEIGHT,
    CONF_CATS,
    CONF_DURATION_ENTITY,
    CONF_MIN_WEIGHT,
    CONF_SMOOTHING,
    CONF_TOLERANCE,
    CONF_VISIT_ENTITY,
    CONF_WEIGHT_ENTITY,
    DEFAULT_MIN_WEIGHT,
    DEFAULT_NAME,
    DEFAULT_SMOOTHING,
    DEFAULT_TOLERANCE,
    DOMAIN,
    UNIDENTIFIED,
)

SENSOR = EntitySelector(EntitySelectorConfig(domain="sensor"))


def _kg(min_v: float, max_v: float, step: float) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(min=min_v, max=max_v, step=step, mode=NumberSelectorMode.BOX, unit_of_measurement="kg")
    )


class LitterCatConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._cats: list[dict[str, Any]] = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_WEIGHT_ENTITY])
            self._abort_if_unique_id_configured()
            self._data = user_input
            return await self.async_step_cat()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): TextSelector(),
                vol.Required(CONF_WEIGHT_ENTITY): SENSOR,
                vol.Optional(CONF_VISIT_ENTITY): SENSOR,
                vol.Optional(CONF_DURATION_ENTITY): SENSOR,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_cat(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_CAT_NAME].strip()
            taken = {c[CONF_CAT_NAME].casefold() for c in self._cats} | {UNIDENTIFIED}
            if not name:
                errors[CONF_CAT_NAME] = "invalid_name"
            elif name.casefold() in taken:
                errors[CONF_CAT_NAME] = "duplicate_name"
            else:
                self._cats.append({CONF_CAT_NAME: name, CONF_CAT_WEIGHT: float(user_input[CONF_CAT_WEIGHT])})
                if user_input.get(CONF_ADD_ANOTHER):
                    return await self.async_step_cat()
                return self.async_create_entry(
                    title=self._data[CONF_NAME],
                    data={**self._data, CONF_CATS: self._cats},
                    options={
                        CONF_TOLERANCE: DEFAULT_TOLERANCE,
                        CONF_SMOOTHING: DEFAULT_SMOOTHING,
                        CONF_MIN_WEIGHT: DEFAULT_MIN_WEIGHT,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_CAT_NAME): TextSelector(),
                vol.Required(CONF_CAT_WEIGHT): _kg(0.5, 15, 0.05),
                vol.Optional(CONF_ADD_ANOTHER, default=len(self._cats) == 0): BooleanSelector(),
            }
        )
        return self.async_show_form(
            step_id="cat",
            data_schema=schema,
            errors=errors,
            description_placeholders={"count": str(len(self._cats) + 1)},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        return LitterCatOptionsFlow()


class LitterCatOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        opts = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(CONF_TOLERANCE, default=opts.get(CONF_TOLERANCE, DEFAULT_TOLERANCE)): _kg(0.1, 5, 0.05),
                vol.Required(CONF_SMOOTHING, default=opts.get(CONF_SMOOTHING, DEFAULT_SMOOTHING)): NumberSelector(
                    NumberSelectorConfig(min=0, max=1, step=0.05, mode=NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_MIN_WEIGHT, default=opts.get(CONF_MIN_WEIGHT, DEFAULT_MIN_WEIGHT)): _kg(0, 10, 0.1),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
