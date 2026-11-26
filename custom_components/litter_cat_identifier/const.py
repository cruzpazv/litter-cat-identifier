"""Constants for Litter Cat Identifier."""

DOMAIN = "litter_cat_identifier"

CONF_WEIGHT_ENTITY = "weight_entity"
CONF_VISIT_ENTITY = "visit_entity"
CONF_DURATION_ENTITY = "duration_entity"
CONF_CATS = "cats"
CONF_CAT_NAME = "name"
CONF_CAT_WEIGHT = "weight"
CONF_ADD_ANOTHER = "add_another"
CONF_TOLERANCE = "tolerance"
CONF_SMOOTHING = "smoothing"
CONF_MIN_WEIGHT = "min_weight"

DEFAULT_NAME = "Litter box"
DEFAULT_TOLERANCE = 0.5  # kg
DEFAULT_SMOOTHING = 0.2  # share of each new reading folded into the learned weight
DEFAULT_MIN_WEIGHT = 1.0  # kg

UNIDENTIFIED = "unidentified"

HISTORY_SIZE = 20  # visits in the last-visit sensor attributes
STORED_HISTORY = 2000  # visits kept on disk (cards fetch them over the websocket API)
WEIGHT_DEBOUNCE = 60  # s, weight-only mode
COUNTER_DELAY = 5  # s, wait for the weight sensor after the counter ticks
WEIGHT_BEFORE_COUNTER = 20  # s, a weight this recent belongs to the visit the counter reports
WEIGHT_WAIT = 60  # s, otherwise wait this long for the weight to arrive after the counter
WEIGHT_SETTLE = 2  # s, after the late weight arrives (the duration may follow)
WEIGHT_FRESHNESS = 600  # s, how old a cached weight may be in counter mode

INACTIVITY_CHECK = 300  # s

CONF_PICTURE = "picture"
CONF_PICTURE_MEDIA = "picture_media"
CONF_REMOVE_PICTURE = "remove_picture"
CONF_CAT = "cat"
CONF_CAT_OPTIONS = "cat_options"
CONF_NOTIFY_TARGETS = "notify_targets"
CONF_NOTIFY_UNIDENTIFIED = "notify_unidentified"
CONF_NOTIFY_HEALTH = "notify_health"
CONF_RECORD_UNIDENTIFIED = "record_unidentified"
CONF_NOTIFY_VISIT = "notify_visit"
CONF_ALERT_HOURS = "alert_hours"
CONF_COLOR = "color"  # cat colour for charts / icons, [r, g, b]

STORAGE_VERSION = 1

SERVICE_REASSIGN = "reassign_last_visit"
SERVICE_RECALIBRATE = "recalibrate_weight"
SERVICE_CLEAR_UNIDENTIFIED = "clear_unidentified_visits"
SERVICE_EXPORT = "export_data"
ATTR_WEIGHT = "weight"
ATTR_SAMPLES = "samples"

LEARN_SAMPLES = 5  # learn towards the median of the latest readings: one odd reading does not drag the weight
PARTIAL_WINDOW = 120  # s after a cat's visit: an unidentified reading is probably that cat half-in
RECALIBRATE_SAMPLES = 5
REASON_PARTIAL = "partial_after_visit"
REASON_REFILL = "refill_or_partial"
REASON_NO_WEIGHT = "no_weight"
ATTR_CAT = "cat"
ATTR_CONFIG_ENTRY_ID = "config_entry_id"
