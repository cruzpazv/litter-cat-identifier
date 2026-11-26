"""Public export of one litter box (cats, settings, state): the stable way for other
integrations (e.g. UAHPET) to import from Litter Cat Identifier without reading its storage."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    CONF_ALERT_HOURS,
    CONF_CAT_NAME,
    CONF_CAT_OPTIONS,
    CONF_CAT_WEIGHT,
    CONF_CATS,
    CONF_COLOR,
    CONF_MIN_WEIGHT,
    CONF_NOTIFY_HEALTH,
    CONF_NOTIFY_TARGETS,
    CONF_NOTIFY_UNIDENTIFIED,
    CONF_NOTIFY_VISIT,
    CONF_PICTURE,
    CONF_RECORD_UNIDENTIFIED,
    CONF_SMOOTHING,
    CONF_TOLERANCE,
    DEFAULT_MIN_WEIGHT,
    DEFAULT_SMOOTHING,
    DEFAULT_TOLERANCE,
    DOMAIN,
    STORAGE_VERSION,
)
from .pictures import owned_file

EXPORT_VERSION = 1  # bump on breaking changes to the format below
STATE_KEYS = {
    "visits_today": dict, "last_visit": dict, "alerted": dict, "history": list,
    "day": str, "daily": dict, "weights": dict, "health": dict,
}


async def async_export(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Everything needed to rebuild this litter box elsewhere, JSON-serialisable.

    cats[].weight is the learned weight; cats[].picture_file is the absolute path of a photo
    stored by this integration (copy it: it goes away with the integration), cats[].picture
    a typed URL / path otherwise.
    """
    if entry.state is ConfigEntryState.LOADED:
        data = entry.runtime_data._as_dict()  # freshest values
    else:
        data = await Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}").async_load() or {}
    opts, cat_opts = entry.options, entry.options.get(CONF_CAT_OPTIONS, {})
    learned = data.get("learned", {})
    cats = []
    for c in entry.data.get(CONF_CATS, []):
        name, o = c[CONF_CAT_NAME], cat_opts.get(c[CONF_CAT_NAME], {})
        picture = o.get(CONF_PICTURE) or None
        file = owned_file(hass, picture)
        if file is not None and not await hass.async_add_executor_job(file.is_file):
            file = None
        cats.append({
            "name": name,
            "weight": round(float(learned.get(name, c[CONF_CAT_WEIGHT])), 3),
            "initial_weight": float(c[CONF_CAT_WEIGHT]),
            "picture": None if owned_file(hass, picture) else picture,
            "picture_file": str(file) if file else None,
            "color": o.get(CONF_COLOR),
            "notify_visit": bool(o.get(CONF_NOTIFY_VISIT, False)),
            "alert_hours": float(o.get(CONF_ALERT_HOURS, 0) or 0),
        })
    return {
        "version": EXPORT_VERSION,
        "name": entry.title,
        "cats": cats,
        "settings": {
            "tolerance": float(opts.get(CONF_TOLERANCE, DEFAULT_TOLERANCE)),
            "smoothing": float(opts.get(CONF_SMOOTHING, DEFAULT_SMOOTHING)),
            "min_weight": float(opts.get(CONF_MIN_WEIGHT, DEFAULT_MIN_WEIGHT)),
            "notify_targets": list(opts.get(CONF_NOTIFY_TARGETS, [])),
            "notify_unidentified": bool(opts.get(CONF_NOTIFY_UNIDENTIFIED, False)),
            "notify_health": bool(opts.get(CONF_NOTIFY_HEALTH, True)),
            "record_unidentified": bool(opts.get(CONF_RECORD_UNIDENTIFIED, True)),
        },
        "state": {key: deepcopy(data.get(key, kind())) for key, kind in STATE_KEYS.items()},
    }
