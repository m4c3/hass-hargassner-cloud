DOMAIN = "hargassner_cloud"
NAME = "Hargassner Cloud"
PLATFORMS = ["sensor"]

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_BASE_URL = "base_url"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_INSTALLATION = "installation"

DEFAULT_BASE_URL = "https://web.hargassner.at"
DEFAULT_SCAN_INTERVAL = 60  # seconds

AUTH_URL = "https://web.hargassner.at/api/auth/login"
WIDGETS_URL_TMPL = "https://web.hargassner.at/api/installations/{installation}/widgets"
