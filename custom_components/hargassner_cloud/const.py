from __future__ import annotations

DOMAIN = "hargassner_cloud"
NAME = "Hargassner Cloud"
PLATFORMS = ["sensor", "binary_sensor"]

# Config keys
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_CLIENT_SECRET = "client_secret"
CONF_CLIENT_ID = "client_id"
CONF_INSTALLATION = "installation"
CONF_BASE_URL = "base_url"
CONF_AREA = "area"

# Options keys
DEFAULT_SCAN_INTERVAL = 300
MIN_SCAN_INTERVAL = 30
DEFAULT_BASE_URL = "https://web.hargassner.at"
# NEW: Options-Override (JSON-Text) für Mapping-Anpassungen pro Entity-Key
# Format:
# {
#   "heater_temp_current": {"widget": "HEATER", "field": "heater_temperature_current"},
#   "hc1_room_temp_current": {"widget": "HEATING_CIRCUIT_RADIATOR", "field": "room_temperature_current", "number": "1"}
# }
CONF_MAPPING_OVERRIDES_JSON = "mapping_overrides_json"
