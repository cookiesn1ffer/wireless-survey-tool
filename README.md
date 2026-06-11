# WireSurvey 📡

A wireless survey and network diagnostics tool for the **Raspberry Pi Zero WH**. Runs a lightweight Flask web server — open the dashboard from any browser on your network.

---

## Features

- **Wi-Fi Scanner** — live scan of nearby networks (SSID, BSSID, channel, band, signal strength, security)
- **Channel Analyzer** — bar chart of channel congestion across all detected networks
- **Signal History** — plot RSSI over time for any network to map coverage
- **Network Diagnostics** — ping, traceroute, DNS lookup, speedtest, interface stats
- **CSV Export** — download a snapshot of the current scan to your browser
- **Auto-start** — runs as a systemd service on boot

---

## Requirements

- Raspberry Pi Zero WH (or any Pi with Wi-Fi)
- Raspberry Pi OS (Bookworm / Debian 12)
- Python 3.10+

---

## Installation

```bash
# 1. Clone the repo onto your Pi
git clone https://github.com/YOUR_USERNAME/wireless-survey-tool.git
cd wireless-survey-tool

# 2. Run the installer (as root)
sudo bash install.sh
```

The installer will:
- Prompt for your Wi-Fi SSID and password
- Install system packages (`iw`, `wireless-tools`, `traceroute`, etc.)
- Install Python dependencies (`flask`, `speedtest-cli`)
- Configure `wpa_supplicant` for your network
- Install and enable a systemd service that starts on boot

---

## Configuration

Edit `config.py` before installing if you prefer to set credentials manually:

```python
WIFI_SSID     = "YOUR_SSID"
WIFI_PASSWORD = "YOUR_PASSWORD"
WIFI_INTERFACE = "wlan0"
PORT = 5000
```

---

## Usage

Once installed, open your browser and navigate to:

```
http://<pi-ip-address>:5000
```

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/` | Overview, top networks, channel chart, quick ping |
| Scanner | `/scanner` | Full network list with filters and CSV export |
| Diagnostics | `/diagnostics` | Ping, traceroute, DNS, speedtest, interface info |
| History | `/history` | Live RSSI chart for tracked networks |

---

## Service Management

```bash
sudo systemctl status  wiresurvey   # check status
sudo systemctl restart wiresurvey   # restart
sudo systemctl stop    wiresurvey   # stop
sudo journalctl -u wiresurvey -f    # live logs
```

---

## Project Structure

```
wireless-survey-tool/
├── app.py                  # Flask app + API routes
├── config.py               # Configuration (credentials, interface, port)
├── requirements.txt        # Python dependencies
├── install.sh              # One-command installer for Raspberry Pi
├── wiresurvey.service      # systemd service file
├── scanner/
│   ├── wifi.py             # Wi-Fi scanner + signal history
│   └── diagnostics.py      # Ping, traceroute, DNS, speedtest
└── templates/
    ├── base.html           # Shared layout + nav
    ├── index.html          # Dashboard
    ├── scanner.html        # Wi-Fi scanner page
    ├── diagnostics.html    # Diagnostics page
    └── history.html        # Signal history page
```

---

## Notes

- The Pi Zero WH's onboard BCM43438 chip does **not** support monitor mode. Passive traffic capture requires an external USB adapter (e.g. Alfa AWUS036ACH).
- The app runs as root to allow `iwlist` scans. This is standard practice for Pi network tools.
- `config.py` is tracked by git with placeholder values — **do not commit real credentials**.
