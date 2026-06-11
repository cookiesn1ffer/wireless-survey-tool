#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  Wireless Survey Tool — Installer for Raspberry Pi Zero WH
# ─────────────────────────────────────────────────────────────
set -e

INSTALL_DIR="/opt/wiresurvey"
SERVICE="wiresurvey"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║      Wireless Survey Tool Setup      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── Root check ────────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
  echo "✗  Please run as root: sudo bash install.sh"
  exit 1
fi

# ── Prompt for Wi-Fi credentials ──────────────────────────────
read -rp "  Wi-Fi SSID     : " WIFI_SSID
read -rsp "  Wi-Fi Password : " WIFI_PASSWORD
echo ""

# ── System packages ───────────────────────────────────────────
echo ""
echo "[1/5] Installing system packages…"
apt-get update -qq
apt-get install -y -qq python3 python3-pip wireless-tools iw net-tools traceroute

# ── Python dependencies ───────────────────────────────────────
echo "[2/5] Installing Python packages…"
pip3 install flask speedtest-cli --break-system-packages -q

# ── Copy app files ────────────────────────────────────────────
echo "[3/5] Copying app to ${INSTALL_DIR}…"
mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR/"
mkdir -p "$INSTALL_DIR/data" "$INSTALL_DIR/logs"

# Patch config.py with entered credentials
sed -i "s/YOUR_SSID/${WIFI_SSID}/g"       "$INSTALL_DIR/config.py"
sed -i "s/YOUR_PASSWORD/${WIFI_PASSWORD}/g" "$INSTALL_DIR/config.py"

# ── Configure Wi-Fi (wpa_supplicant) ──────────────────────────
echo "[4/5] Configuring Wi-Fi…"
cat >> /etc/wpa_supplicant/wpa_supplicant.conf <<EOF

network={
    ssid="${WIFI_SSID}"
    psk="${WIFI_PASSWORD}"
    key_mgmt=WPA-PSK
}
EOF
wpa_cli -i wlan0 reconfigure 2>/dev/null || true

# ── systemd service ───────────────────────────────────────────
echo "[5/5] Installing systemd service…"
cp "$INSTALL_DIR/wiresurvey.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable "$SERVICE"
systemctl start  "$SERVICE"

# ── Done ──────────────────────────────────────────────────────
echo ""
echo "✓  WireSurvey installed and running!"
echo ""
echo "   Open in your browser:"
echo "   → http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "   Service commands:"
echo "   sudo systemctl status  wiresurvey"
echo "   sudo systemctl restart wiresurvey"
echo "   sudo journalctl -u wiresurvey -f"
echo ""
