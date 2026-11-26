from datetime import timedelta
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component
from PIL import Image
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.litter_cat_identifier.pictures import LEGACY_PREFIX, URL_PREFIX, owned_file, picture_url

from .test_integration import _setup


async def _edit_cat(hass, entry, data):
    r = await hass.config_entries.options.async_init(entry.entry_id)
    r = await hass.config_entries.options.async_configure(r["flow_id"], {"next_step_id": "cat_select"})
    r = await hass.config_entries.options.async_configure(r["flow_id"], {"cat": "Luna"})
    base = {"notify_visit": False, "alert_hours": 0}
    return await hass.config_entries.options.async_configure(r["flow_id"], {**base, **data})


async def test_pick_photo_from_media(hass: HomeAssistant, tmp_path: Path, hass_client, hass_client_no_auth, freezer):
    media = tmp_path / "media"
    media.mkdir()
    Image.new("RGB", (1200, 800), (200, 120, 40)).save(media / "luna.png")
    (media / "notes.txt").write_text("not an image")
    hass.config.media_dirs = {"local": str(media)}
    assert await async_setup_component(hass, "media_source", {})

    entry = await _setup(hass)

    # picking a photo stores a square 512 px JPEG and serves it
    r = await _edit_cat(hass, entry, {"picture_media": {
        "media_content_id": "media-source://media_source/local/luna.png", "media_content_type": "image/png"}})
    assert r["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    url = hass.states.get("sensor.taco_luna_weight").attributes["entity_picture"]
    assert url.startswith(URL_PREFIX + "/")
    first = owned_file(hass, url)
    with Image.open(first) as img:
        assert img.size == (512, 512)
    assert "authSig=" in url  # handed out signed
    exported = await hass.services.async_call(
        "litter_cat_identifier", "export_data", {"config_entry_id": entry.entry_id}, blocking=True, return_response=True
    )
    luna = next(c for c in exported["cats"] if c["name"] == "Luna")
    assert luna["picture_file"] == str(first) and luna["picture"] is None
    # logged in or signed: served; neither (or a guessed / bad name): refused
    assert (await (await hass_client()).get(url.split("?")[0])).status == 200
    anon = await hass_client_no_auth()
    assert (await anon.get(url)).status == 200
    assert (await anon.get(url.split("?")[0])).status == 401
    assert (await anon.get(f"{LEGACY_PREFIX}/{first.name}")).status == 404  # the old static path is gone
    assert (await (await hass_client()).get(f"{URL_PREFIX}/000000000000.jpg")).status == 404
    # the same signed URL is reused (no state churn), and stored legacy URLs still map to the file
    assert picture_url(hass, url.split("?")[0]) == url
    assert picture_url(hass, f"{LEGACY_PREFIX}/{first.name}?v=1") == url
    # signed URLs expire after 2 days: entities hand out a fresh one in time
    freezer.tick(timedelta(days=1, hours=7))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    fresh = hass.states.get("sensor.taco_luna_weight").attributes["entity_picture"]
    assert fresh != url
    freezer.tick(timedelta(hours=18))
    assert (await anon.get(url)).status == 401
    assert (await anon.get(fresh)).status == 200

    # a non-image is rejected with a form error, nothing changes
    r = await _edit_cat(hass, entry, {"picture_media": {
        "media_content_id": "media-source://media_source/local/notes.txt", "media_content_type": "text/plain"}})
    assert r["type"] is FlowResultType.FORM and r["errors"] == {"picture_media": "invalid_image"}

    # replacing the photo deletes the old file
    r = await _edit_cat(hass, entry, {"picture_media": {
        "media_content_id": "media-source://media_source/local/luna.png", "media_content_type": "image/png"}})
    await hass.async_block_till_done()
    second = owned_file(hass, hass.states.get("sensor.taco_luna_weight").attributes["entity_picture"])
    assert second.exists() and not first.exists()

    # remove photo
    r = await _edit_cat(hass, entry, {"remove_picture": True})
    await hass.async_block_till_done()
    assert "entity_picture" not in hass.states.get("sensor.taco_luna_weight").attributes
    assert not second.exists()

    # typed URL still works
    await _edit_cat(hass, entry, {"picture": "/local/cats/luna.jpg"})
    await hass.async_block_till_done()
    assert hass.states.get("sensor.taco_luna_weight").attributes["entity_picture"] == "/local/cats/luna.jpg"


def test_owned_file_rejects_traversal(hass: HomeAssistant):
    assert owned_file(hass, f"{URL_PREFIX}/../secrets.yaml") is None
    assert owned_file(hass, f"{LEGACY_PREFIX}/..%2Fsecrets.yaml") is None
    assert owned_file(hass, "/local/x.jpg") is None
    assert picture_url(hass, "/local/x.jpg") == "/local/x.jpg"
