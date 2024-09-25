"""Constants for eto_irrigation."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "eto_smart_zone"
DEFAULT_NAME = "ETO Smart Zone"
ATTRIBUTION = "Data provided by OWM and calculations"
MANUFACTURER = "DPK"
CONFIG_FLOW_VERSION = 1

DEFAULT_NAME = "ETO"
DEFAULT_RETRY = 60

# entities for data
CONF_ETO_ENTITY_ID = "eto_entity_id"
CONF_RAIN_ENTITY_ID = "rain_entity_id"
CONF_SCALE = "scale"
CONF_MAX_MINS = "max_mins"
CONF_THROUGHPUT_MM_H = "throughput_mm_h"

ATTR_ETO = "eto"
ATTR_RAIN = "rain"
CALC_RAW_RUNTIME = "raw_runtime"
CALC_RUNTIME = "runtime"
