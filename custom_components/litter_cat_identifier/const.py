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
DEFAULT_TOLERANCE = 1.0  # kg
DEFAULT_SMOOTHING = 0.2  # share of each new reading folded into the learned weight
DEFAULT_MIN_WEIGHT = 1.0  # kg

UNIDENTIFIED = "unidentified"

HISTORY_SIZE = 20
WEIGHT_DEBOUNCE = 60  # s, weight-only mode
COUNTER_DELAY = 5  # s, wait for the weight sensor after the counter ticks
WEIGHT_FRESHNESS = 600  # s, how old a cached weight may be in counter mode

INACTIVITY_CHECK = 300  # s

CONF_PICTURE = "picture"
CONF_CAT = "cat"
CONF_CAT_OPTIONS = "cat_options"
CONF_NOTIFY_TARGETS = "notify_targets"
CONF_NOTIFY_UNIDENTIFIED = "notify_unidentified"
CONF_NOTIFY_VISIT = "notify_visit"
CONF_ALERT_HOURS = "alert_hours"

STORAGE_VERSION = 1

SERVICE_REASSIGN = "reassign_last_visit"
ATTR_CAT = "cat"
ATTR_CONFIG_ENTRY_ID = "config_entry_id"
