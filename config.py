# ─────────────────────────────────────────────
#  Wireless Survey Tool — Configuration
# ─────────────────────────────────────────────

# Wi-Fi credentials for the network the Pi connects to
WIFI_SSID     = "YOUR_SSID"
WIFI_PASSWORD = "YOUR_PASSWORD"

# Network interface used for scanning / diagnostics
WIFI_INTERFACE = "wlan0"

# Flask web server
HOST = "0.0.0.0"
PORT = 5000
DEBUG = False

# Signal history — how many readings to keep in memory per SSID
HISTORY_MAX_POINTS = 120   # ~10 minutes at 5-second intervals
SCAN_INTERVAL_SECONDS = 5

# Log directory for CSV exports
LOG_DIR = "data"
