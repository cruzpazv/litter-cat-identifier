"""Config and options flow."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    MediaSelector,
    MediaSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .const import (
    CONF_ADD_ANOTHER,
    CONF_ALERT_HOURS,
    CONF_CAT,
    CONF_CAT_NAME,
    CONF_CAT_OPTIONS,
    CONF_CAT_WEIGHT,
    CONF_CATS,
    CONF_DURATION_ENTITY,
    CONF_MIN_WEIGHT,
    CONF_NOTIFY_TARGETS,
    CONF_NOTIFY_HEALTH,
    CONF_NOTIFY_UNIDENTIFIED,
    CONF_NOTIFY_VISIT,
    CONF_RECORD_UNIDENTIFIED,
    CONF_PICTURE,
    CONF_PICTURE_MEDIA,
    CONF_REMOVE_PICTURE,
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
from .pictures import PictureError, async_delete_pictures, async_store_picture

SENSOR = EntitySelector(EntitySelectorConfig(domain="sensor"))
# A visit counter sensor, or a visit event entity carrying weight / duration (e.g. UAHPET).
VISIT = EntitySelector(EntitySelectorConfig(domain=["sensor", "event"]))
PHOTO = MediaSelector(MediaSelectorConfig(accept=["image/*"]))


async def _resolve_picture(hass, user_input: dict[str, Any], current: str | None) -> str | None:
    """Media pick > typed URL/path > keep current. Raises PictureError."""
    media = user_input.get(CONF_PICTURE_MEDIA)
    if media and media.get("media_content_id"):
        return await async_store_picture(hass, media["media_content_id"])
    typed = _picture(user_input.get(CONF_PICTURE))
    return typed if typed is not None else current


def _uahpet_suggestion(hass: HomeAssistant) -> dict[str, Any]:
    """Pre-fill the form from a UAHPET litter box that no entry uses yet."""
    used = set()
    for entry in hass.config_entries.async_entries(DOMAIN):
        used |= {entry.data.get(CONF_VISIT_ENTITY), entry.data.get(CONF_WEIGHT_ENTITY)}
    by_device: dict[str, dict[str, str]] = {}
    for ent in er.async_get(hass).entities.values():
        if ent.platform == "uahpet" and ent.device_id and ent.translation_key in ("visit", "last_cat_weight", "last_visit_duration"):
            by_device.setdefault(ent.device_id, {})[ent.translation_key] = ent.entity_id
    for device_id, keys in by_device.items():
        if "visit" not in keys or "last_cat_weight" not in keys or keys["visit"] in used:
            continue
        device = dr.async_get(hass).async_get(device_id)
        out = {
            CONF_NAME: (device.name_by_user or device.name) if device else DEFAULT_NAME,
            CONF_WEIGHT_ENTITY: keys["last_cat_weight"],
            CONF_VISIT_ENTITY: keys["visit"],
        }
        if "last_visit_duration" in keys:
            out[CONF_DURATION_ENTITY] = keys["last_visit_duration"]
        return out
    return {}


def _kg(min_v: float, max_v: float, step: float) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(min=min_v, max=max_v, step=step, mode=NumberSelectorMode.BOX, unit_of_measurement="kg")
    )


def _picture(value: Any) -> str | None:
    value = (value or "").strip()
    return value or None


class LitterCatConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._cats: list[dict[str, Any]] = []
        self._cat_options: dict[str, dict[str, Any]] = {}

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
                vol.Optional(CONF_VISIT_ENTITY): VISIT,
                vol.Optional(CONF_DURATION_ENTITY): SENSOR,
            }
        )
        # A UAHPET litter box is recognised and its visit event / weight / duration filled in.
        schema = self.add_suggested_values_to_schema(schema, _uahpet_suggestion(self.hass))
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
                try:
                    picture = await _resolve_picture(self.hass, user_input, None)
                except PictureError as err:
                    errors[CONF_PICTURE_MEDIA] = str(err)
            if not errors:
                self._cats.append({CONF_CAT_NAME: name, CONF_CAT_WEIGHT: float(user_input[CONF_CAT_WEIGHT])})
                self._cat_options[name] = {CONF_PICTURE: picture}
                if user_input.get(CONF_ADD_ANOTHER):
                    return await self.async_step_cat()
                return self.async_create_entry(
                    title=self._data[CONF_NAME],
                    data={**self._data, CONF_CATS: self._cats},
                    options={
                        CONF_TOLERANCE: DEFAULT_TOLERANCE,
                        CONF_SMOOTHING: DEFAULT_SMOOTHING,
                        CONF_MIN_WEIGHT: DEFAULT_MIN_WEIGHT,
                        CONF_CAT_OPTIONS: self._cat_options,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_CAT_NAME): TextSelector(),
                vol.Required(CONF_CAT_WEIGHT): _kg(0.5, 15, 0.05),
                vol.Optional(CONF_PICTURE_MEDIA): PHOTO,
                vol.Optional(CONF_PICTURE): TextSelector(),
                vol.Optional(CONF_ADD_ANOTHER, default=len(self._cats) == 0): BooleanSelector(),
            }
        )
        return self.async_show_form(
            step_id="cat",
            data_schema=schema,
            errors=errors,
            description_placeholders={"count": str(len(self._cats) + 1)},
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Swap the litter box sensors. Cats, learned weights and history are kept (stored per entry)."""
        entry = self._get_reconfigure_entry()
        sensor_keys = (CONF_WEIGHT_ENTITY, CONF_VISIT_ENTITY, CONF_DURATION_ENTITY)
        errors: dict[str, str] = {}
        if user_input is not None:
            weight = user_input[CONF_WEIGHT_ENTITY]
            if any(e.unique_id == weight and e.entry_id != entry.entry_id for e in self._async_current_entries()):
                errors[CONF_WEIGHT_ENTITY] = "weight_in_use"
            else:
                data = {k: v for k, v in entry.data.items() if k not in sensor_keys}
                data.update({k: user_input[k] for k in sensor_keys if user_input.get(k)})
                return self.async_update_reload_and_abort(entry, unique_id=weight, data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_WEIGHT_ENTITY): SENSOR,
                vol.Optional(CONF_VISIT_ENTITY): VISIT,
                vol.Optional(CONF_DURATION_ENTITY): SENSOR,
            }
        )
        suggested = user_input or {k: entry.data[k] for k in sensor_keys if entry.data.get(k)}
        return self.async_show_form(
            step_id="reconfigure", data_schema=self.add_suggested_values_to_schema(schema, suggested), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        return LitterCatOptionsFlow()


class LitterCatOptionsFlow(OptionsFlow):
    def __init__(self) -> None:
        self._cat: str | None = None

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(step_id="init", menu_options=["settings", "cat_select"])

    async def async_step_settings(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        opts = self.config_entry.options
        if user_input is not None:
            return self.async_create_entry(data={**opts, **user_input})

        current = list(opts.get(CONF_NOTIFY_TARGETS, []))
        services = sorted(
            {f"notify.{s}" for s in self.hass.services.async_services_for_domain("notify")} | set(current)
        )
        schema = vol.Schema(
            {
                vol.Required(CONF_TOLERANCE, default=opts.get(CONF_TOLERANCE, DEFAULT_TOLERANCE)): _kg(0.1, 5, 0.05),
                vol.Required(CONF_SMOOTHING, default=opts.get(CONF_SMOOTHING, DEFAULT_SMOOTHING)): NumberSelector(
                    NumberSelectorConfig(min=0, max=1, step=0.05, mode=NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_MIN_WEIGHT, default=opts.get(CONF_MIN_WEIGHT, DEFAULT_MIN_WEIGHT)): _kg(0, 10, 0.1),
                vol.Optional(CONF_NOTIFY_TARGETS, default=current): SelectSelector(
                    SelectSelectorConfig(
                        options=services, multiple=True, custom_value=True, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Required(
                    CONF_RECORD_UNIDENTIFIED, default=opts.get(CONF_RECORD_UNIDENTIFIED, True)
                ): BooleanSelector(),
                vol.Required(
                    CONF_NOTIFY_UNIDENTIFIED, default=opts.get(CONF_NOTIFY_UNIDENTIFIED, False)
                ): BooleanSelector(),
                vol.Required(CONF_NOTIFY_HEALTH, default=opts.get(CONF_NOTIFY_HEALTH, True)): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="settings", data_schema=schema)

    async def async_step_cat_select(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._cat = user_input[CONF_CAT]
            return await self.async_step_cat_edit()

        names = [c[CONF_CAT_NAME] for c in self.config_entry.data[CONF_CATS]]
        schema = vol.Schema(
            {vol.Required(CONF_CAT): SelectSelector(SelectSelectorConfig(options=names, mode=SelectSelectorMode.LIST))}
        )
        return self.async_show_form(step_id="cat_select", data_schema=schema)

    async def async_step_cat_edit(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        opts = self.config_entry.options
        cat_opts = dict(opts.get(CONF_CAT_OPTIONS, {}))
        current = cat_opts.get(self._cat, {})

        errors: dict[str, str] = {}
        if user_input is not None:
            old = current.get(CONF_PICTURE)
            try:
                if user_input.get(CONF_REMOVE_PICTURE):
                    picture = None
                else:
                    # an emptied URL field means "no typed URL", not "remove"
                    typed = _picture(user_input.get(CONF_PICTURE))
                    picture = await _resolve_picture(
                        self.hass, user_input, typed if typed is not None else old
                    )
            except PictureError as err:
                errors[CONF_PICTURE_MEDIA] = str(err)
            if not errors:
                if picture != old:
                    await async_delete_pictures(self.hass, [old])
                cat_opts[self._cat] = {
                    CONF_PICTURE: picture,
                    CONF_NOTIFY_VISIT: user_input[CONF_NOTIFY_VISIT],
                    CONF_ALERT_HOURS: float(user_input[CONF_ALERT_HOURS]),
                }
                return self.async_create_entry(data={**opts, CONF_CAT_OPTIONS: cat_opts})

        schema = vol.Schema(
            {
                vol.Optional(CONF_PICTURE_MEDIA): PHOTO,
                vol.Optional(CONF_PICTURE, description={"suggested_value": current.get(CONF_PICTURE)}): TextSelector(),
                vol.Optional(CONF_REMOVE_PICTURE, default=False): BooleanSelector(),
                vol.Required(CONF_NOTIFY_VISIT, default=current.get(CONF_NOTIFY_VISIT, False)): BooleanSelector(),
                vol.Required(CONF_ALERT_HOURS, default=current.get(CONF_ALERT_HOURS, 0)): NumberSelector(
                    NumberSelectorConfig(min=0, max=168, step=1, mode=NumberSelectorMode.BOX, unit_of_measurement="h")
                ),
            }
        )
        return self.async_show_form(
            step_id="cat_edit", data_schema=schema, errors=errors, description_placeholders={"cat": self._cat}
        )
