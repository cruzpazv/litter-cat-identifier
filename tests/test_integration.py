from datetime import timedelta

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed, async_mock_service

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


async def test_pictures_and_notifications(hass: HomeAssistant, freezer):
    calls = async_mock_service(hass, "notify", "mobile_app_phone")
    entry = await _setup(hass)

    # general settings: notify target + unidentified alerts
    r = await hass.config_entries.options.async_init(entry.entry_id)
    assert r["type"] is FlowResultType.MENU
    r = await hass.config_entries.options.async_configure(r["flow_id"], {"next_step_id": "settings"})
    sel = next(v for k, v in r["data_schema"].schema.items() if k == "notify_targets")
    assert "notify.mobile_app_phone" in sel.config["options"]
    r = await hass.config_entries.options.async_configure(
        r["flow_id"],
        {"tolerance": 1.0, "smoothing": 0.2, "min_weight": 1.0,
         "notify_targets": ["notify.mobile_app_phone"], "notify_unidentified": True},
    )
    assert r["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    # per-cat: photo, notify on visit, alert after 1 h
    r = await hass.config_entries.options.async_init(entry.entry_id)
    r = await hass.config_entries.options.async_configure(r["flow_id"], {"next_step_id": "cat_select"})
    r = await hass.config_entries.options.async_configure(r["flow_id"], {"cat": "Luna"})
    assert r["step_id"] == "cat_edit"
    r = await hass.config_entries.options.async_configure(
        r["flow_id"], {"picture": " /local/gatos/luna.jpg ", "notify_visit": True, "alert_hours": 1}
    )
    assert r["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["notify_targets"] == ["notify.mobile_app_phone"]  # settings kept

    assert hass.states.get("sensor.taco_luna_weight").attributes["entity_picture"] == "/local/gatos/luna.jpg"
    assert "entity_picture" not in hass.states.get("sensor.taco_simba_weight").attributes

    await _visit(hass, 3.9, 1)
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["message"] == "Luna used the litter box (3.90 kg)."
    assert calls[0].data["data"]["image"] == "/local/gatos/luna.jpg"
    assert hass.states.get("sensor.taco_last_visit").attributes["entity_picture"] == "/local/gatos/luna.jpg"

    await _visit(hass, 5.4, 2)   # Simba: notify_visit off
    await hass.async_block_till_done()
    assert len(calls) == 1

    await _visit(hass, 9.0, 3)   # unidentified
    await hass.async_block_till_done()
    assert len(calls) == 2 and "Unidentified reading (9.00 kg)" in calls[1].data["message"]

    # inactivity: one alert only, re-armed by the next visit
    freezer.tick(timedelta(hours=2))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    freezer.tick(timedelta(minutes=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    alerts = [c for c in calls if "over 1 h" in c.data["message"]]
    assert len(alerts) == 1


def test_messages_es():
    from custom_components.litter_cat_identifier.messages import text

    assert text("es", "visit", cat="Luna", weight=3.9) == "Luna ha usado el arenero (3.90 kg)."
    assert text("es", "unidentified_refill_or_partial", weight=None, cat="") == (
        "Lectura no identificada: probablemente relleno de arena o un gato medio dentro."
    )
    assert text("es", "unidentified_partial_after_visit", weight=2.1, cat="Mochi") == (
        "Lectura no identificada (2.10 kg): probablemente Mochi medio dentro, justo tras su visita."
    )
    assert text("fr", "inactive", cat="Luna", hours="24") == "Luna hasn't used the litter box for over 24 h."


async def test_grams(hass: HomeAssistant):
    await _setup(hass)
    hass.states.async_set(WEIGHT, "3700", {"unit_of_measurement": "g"})
    hass.states.async_set(COUNTER, "1")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=6))
    await hass.async_block_till_done()
    assert hass.states.get("sensor.taco_last_visit").state == "Luna"


async def test_unidentified_reasons(hass: HomeAssistant, freezer):
    await _setup(hass)
    await _visit(hass, 3.9, 1)                 # Luna
    freezer.tick(timedelta(seconds=30))
    await _visit(hass, 1.6, 2)                 # 30 s later, half a cat
    last = hass.states.get("sensor.taco_last_visit")
    assert last.state == "unidentified"
    assert last.attributes["reason"] == "partial_after_visit"
    assert last.attributes["likely_cat"] == "Luna"

    freezer.tick(timedelta(minutes=30))
    await _visit(hass, 9.5, 3)                 # much later, too heavy
    last = hass.states.get("sensor.taco_last_visit")
    assert last.attributes["reason"] == "refill_or_partial"
    assert last.attributes["likely_cat"] is None

    # reassigning clears the guess
    await hass.services.async_call(DOMAIN, "reassign_last_visit", {"cat": "Simba"}, blocking=True)
    hist = hass.states.get("sensor.taco_last_visit").attributes["history"]
    assert "reason" not in hist[0]


async def test_recalibrate(hass: HomeAssistant):
    await _setup(hass)
    for i, kg in enumerate((4.30, 4.40, 4.35, 9.0, 4.45), start=1):
        await _visit(hass, kg, i)
    # Luna learned slowly from 3.8; recalibrating jumps to the median of her readings
    btn = "button.taco_recalibrate_luna_weight"
    assert hass.states.get(btn) is not None
    await hass.services.async_call("button", "press", {"entity_id": btn}, blocking=True)
    assert float(hass.states.get("sensor.taco_luna_weight").state) == pytest.approx(4.375)

    await hass.services.async_call(DOMAIN, "recalibrate_weight", {"cat": "Luna", "samples": 2}, blocking=True)
    assert float(hass.states.get("sensor.taco_luna_weight").state) == pytest.approx(4.40)

    await hass.services.async_call(DOMAIN, "recalibrate_weight", {"cat": "Simba", "weight": 5.8}, blocking=True)
    assert float(hass.states.get("sensor.taco_simba_weight").state) == pytest.approx(5.8)

    # Simba has no weighed visits: the button explains instead of guessing
    from homeassistant.exceptions import HomeAssistantError
    await hass.services.async_call(DOMAIN, "recalibrate_weight", {"cat": "Simba", "weight": 5.5}, blocking=True)
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "button", "press", {"entity_id": "button.taco_recalibrate_simba_weight"}, blocking=True
        )


async def test_cards_served(hass: HomeAssistant, hass_client):
    await _setup(hass)
    assert hass.states.get("sensor.taco_luna_weight").attributes["cat"] == "Luna"
    assert hass.states.get("sensor.taco_simba_visits_today").attributes["cat"] == "Simba"
    client = await hass_client()
    resp = await client.get("/litter_cat_identifier_static/litter-cat-identifier-cards.js")
    assert resp.status == 200
    assert "litter-cat-identifier-cats" in await resp.text()
