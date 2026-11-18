"""UAHPET context, live-scale repair, auto-fill and per-cat health."""

from datetime import date, timedelta

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er, issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.litter_cat_identifier import health
from custom_components.litter_cat_identifier.const import DOMAIN

from .test_integration import COUNTER, WEIGHT, _setup, _visit


def test_health_rules():
    assert not health.frequent_visits(9, [3, 3, 4])  # not enough history
    assert health.frequent_visits(8, [3, 3, 4, 3, 3])
    assert not health.frequent_visits(5, [3, 3, 4, 3, 3])
    assert health.long_visit(200, [40, 45, 50, 38, 42])
    assert not health.long_visit(100, [40, 45, 50, 38, 42])  # below the 120 s floor
    today = date(2026, 11, 18)
    snaps = {(today - timedelta(days=d)).isoformat(): 5.5 for d in (40, 30, 22)}
    assert health.weight_loss(5.2, snaps, today) == 5.5
    assert health.weight_loss(5.4, snaps, today) is None


def _uahpet_device(hass: HomeAssistant) -> dict[str, str]:
    """Fake UAHPET litter box entities on one device."""
    src = MockConfigEntry(domain="uahpet")
    src.add_to_hass(hass)
    dev = dr.async_get(hass).async_get_or_create(config_entry_id=src.entry_id, identifiers={("uahpet", "box")}, name="TACo")
    reg = er.async_get(hass)
    ids = {}
    for domain, key in [("event", "visit"), ("sensor", "last_cat_weight"), ("sensor", "last_visit_duration"),
                        ("sensor", "work_status"), ("binary_sensor", "stagnant")]:
        ent = reg.async_get_or_create(domain, "uahpet", f"box_{key}", device_id=dev.id, translation_key=key,
                                      suggested_object_id=f"taco_{key}", config_entry=src)
        ids[key] = ent.entity_id
    hass.states.async_set(ids["last_cat_weight"], "0", {"unit_of_measurement": "kg"})
    hass.states.async_set(ids["visit"], "unknown", {})
    hass.states.async_set(ids["work_status"], "standby")
    hass.states.async_set(ids["stagnant"], "off")
    return ids


async def test_autofill_from_uahpet(hass: HomeAssistant):
    ids = _uahpet_device(hass)
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    suggested = {str(k): k.description.get("suggested_value") for k in r["data_schema"].schema if k.description}
    assert suggested["visit_entity"] == ids["visit"]
    assert suggested["weight_entity"] == ids["last_cat_weight"]
    assert suggested["duration_entity"] == ids["last_visit_duration"]
    assert suggested["name"] == "TACo"


async def test_device_reasons_for_unidentified(hass: HomeAssistant):
    ids = _uahpet_device(hass)
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"name": "TACo", "weight_entity": ids["last_cat_weight"], "visit_entity": ids["visit"]})
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"name": "Luna", "weight": 3.8, "add_another": False})
    await hass.async_block_till_done()

    hass.states.async_set(ids["work_status"], "leveling")
    hass.states.async_set(ids["visit"], "2026-11-18T10:00:00+00:00", {"event_type": "visit", "weight": 1.2, "duration": 5})
    await hass.async_block_till_done()
    assert hass.states.get("sensor.taco_last_visit").attributes["reason"] == "device_busy"

    hass.states.async_set(ids["work_status"], "standby")
    hass.states.async_set(ids["stagnant"], "on")
    hass.states.async_set(ids["visit"], "2026-11-18T11:00:00+00:00", {"event_type": "visit", "weight": 7.5, "duration": 400})
    await hass.async_block_till_done()
    assert hass.states.get("sensor.taco_last_visit").attributes["reason"] == "stayed_too_long"


async def test_live_scale_issue(hass: HomeAssistant):
    entry = await _setup(hass)  # counter mode on a plain weight sensor
    for i, kg in enumerate([4.0, 0, 3.9, 0, 5.4, 0], start=1):
        hass.states.async_set(WEIGHT, str(kg), {"unit_of_measurement": "kg"})
        await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"live_scale_{entry.entry_id}") is not None


async def test_frequent_visits_health(hass: HomeAssistant):
    entry = await _setup(hass)
    coordinator = entry.runtime_data
    today = date.today()
    coordinator.daily = {(today - timedelta(days=d)).isoformat(): {"Luna": 2, "Simba": 2} for d in range(1, 8)}
    sensor = "binary_sensor.taco_luna_health"
    assert hass.states.get(sensor).state == "off"
    for n in range(1, 6):
        await _visit(hass, 3.9, n)
    state = hass.states.get(sensor)
    assert state.state == "on" and state.attributes["reasons"] == ["frequent_visits"]
    assert COUNTER  # same helpers as the main tests


async def test_cat_colour(hass: HomeAssistant):
    entry = await _setup(hass)
    r = await hass.config_entries.options.async_init(entry.entry_id)
    r = await hass.config_entries.options.async_configure(r["flow_id"], {"next_step_id": "cat_select"})
    r = await hass.config_entries.options.async_configure(r["flow_id"], {"cat": "Luna"})
    r = await hass.config_entries.options.async_configure(r["flow_id"], {"notify_visit": False, "alert_hours": 0, "color": [89, 161, 79]})
    await hass.async_block_till_done()
    assert hass.states.get("sensor.taco_luna_weight").attributes["color"] == "#59a14f"
