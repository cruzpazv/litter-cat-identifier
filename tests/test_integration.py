from datetime import timedelta

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.litter_cat_identifier.const import DOMAIN

WEIGHT = "sensor.box_weight"
COUNTER = "sensor.box_visits"
DURATION = "sensor.box_duration"


async def _setup(hass: HomeAssistant, with_counter: bool = True):
    hass.states.async_set(WEIGHT, "0", {"unit_of_measurement": "kg"})
    hass.states.async_set(COUNTER, "0")
    hass.states.async_set(DURATION, "0")

    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert r["type"] is FlowResultType.FORM and r["step_id"] == "user"
    data = {"name": "TACo", "weight_entity": WEIGHT, "duration_entity": DURATION}
    if with_counter:
        data["visit_entity"] = COUNTER
    r = await hass.config_entries.flow.async_configure(r["flow_id"], data)
    assert r["step_id"] == "cat"
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"name": "Luna", "weight": 3.8, "add_another": True})
    assert r["step_id"] == "cat"
    # duplicate name rejected
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"name": "luna", "weight": 5, "add_another": False})
    assert r["errors"] == {"name": "duplicate_name"}
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"name": "Simba", "weight": 5.5, "add_another": False})
    assert r["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    return r["result"]


def _ids(hass):
    return sorted(s.entity_id for s in hass.states.async_all() if s.entity_id.startswith(("sensor.taco", "event.taco")))


async def _visit(hass, kg, count, duration=30):
    hass.states.async_set(WEIGHT, str(kg), {"unit_of_measurement": "kg"})
    hass.states.async_set(DURATION, str(duration))
    hass.states.async_set(COUNTER, str(count))
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=6))
    await hass.async_block_till_done()


async def test_counter_mode(hass: HomeAssistant):
    entry = await _setup(hass)
    print(_ids(hass))

    await _visit(hass, 3.9, 1)
    await _visit(hass, 3.9, 2)          # same weight twice: still two visits
    await _visit(hass, 5.3, 3, 45)
    await _visit(hass, 9.0, 4)          # nobody

    assert hass.states.get("sensor.taco_last_visit").state == "unidentified"
    assert hass.states.get("sensor.taco_luna_visits_today").state == "2"
    assert hass.states.get("sensor.taco_simba_visits_today").state == "1"
    assert hass.states.get("sensor.taco_unidentified_visits_today").state == "1"
    assert float(hass.states.get("sensor.taco_luna_weight").state) > 3.8
    hist = hass.states.get("sensor.taco_last_visit").attributes["history"]
    assert [v["cat"] for v in hist] == ["unidentified", "Simba", "Luna", "Luna"]
    assert hist[1]["duration"] == 45
    assert hass.states.get("event.taco_visit").attributes["event_type"] == "unidentified"

    # counter reset to 0 is not a visit
    hass.states.async_set(COUNTER, "0")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=12))
    await hass.async_block_till_done()
    assert len(hass.states.get("sensor.taco_last_visit").attributes["history"]) == 4

    # fix the last visit
    await hass.services.async_call(DOMAIN, "reassign_last_visit", {"cat": "Simba"}, blocking=True)
    assert hass.states.get("sensor.taco_last_visit").state == "Simba"
    assert hass.states.get("sensor.taco_simba_visits_today").state == "2"
    assert hass.states.get("sensor.taco_unidentified_visits_today").state == "0"

    # state survives reload
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.taco_luna_visits_today").state == "2"


async def test_weight_only_mode(hass: HomeAssistant):
    await _setup(hass, with_counter=False)
    hass.states.async_set(WEIGHT, "5.4", {"unit_of_measurement": "kg"})
    await hass.async_block_till_done()
    hass.states.async_set(WEIGHT, "5.6", {"unit_of_measurement": "kg"})  # settling
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=61))
    await hass.async_block_till_done()
    assert hass.states.get("sensor.taco_simba_visits_today").state == "1"
    assert len(hass.states.get("sensor.taco_last_visit").attributes["history"]) == 1


async def test_grams(hass: HomeAssistant):
    await _setup(hass)
    hass.states.async_set(WEIGHT, "3700", {"unit_of_measurement": "g"})
    hass.states.async_set(COUNTER, "1")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=6))
    await hass.async_block_till_done()
    assert hass.states.get("sensor.taco_last_visit").state == "Luna"
