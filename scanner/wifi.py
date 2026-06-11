"""
Wi-Fi scanner — wraps iwlist/iw scan and maintains signal history.
Requires root (sudo) to trigger active scans.
"""

import re
import subprocess
import time
import threading
from collections import defaultdict, deque
from config import WIFI_INTERFACE, HISTORY_MAX_POINTS, SCAN_INTERVAL_SECONDS


# ── In-memory state ──────────────────────────────────────────────────────────

_networks: list[dict] = []          # latest scan results
_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=HISTORY_MAX_POINTS))
_lock = threading.Lock()
_last_scan_time: float = 0.0
_scan_error: str = ""


# ── Parsing ──────────────────────────────────────────────────────────────────

def _parse_iwlist(raw: str) -> list[dict]:
    """Parse iwlist scan output into a list of network dicts."""
    networks = []
    current: dict = {}

    for line in raw.splitlines():
        line = line.strip()

        if line.startswith("Cell "):
            if current:
                networks.append(current)
            current = {}
            m = re.search(r"Address:\s*([0-9A-Fa-f:]{17})", line)
            if m:
                current["bssid"] = m.group(1).upper()

        elif "ESSID:" in line:
            m = re.search(r'ESSID:"(.*?)"', line)
            current["ssid"] = m.group(1) if m else "<hidden>"

        elif "Frequency:" in line:
            m = re.search(r"Frequency:([\d.]+)\s*GHz.*Channel\s*(\d+)", line)
            if m:
                freq = float(m.group(1))
                current["channel"] = int(m.group(2))
                current["band"] = "5 GHz" if freq >= 5.0 else "2.4 GHz"

        elif "Signal level=" in line:
            m = re.search(r"Signal level=(-?\d+)\s*dBm", line)
            if m:
                current["rssi"] = int(m.group(1))

        elif "Encryption key:" in line:
            current["encrypted"] = "on" in line

        elif "IE: IEEE 802.11i/WPA2" in line:
            current["security"] = "WPA2"
        elif "IE: WPA" in line:
            current.setdefault("security", "WPA")

    if current:
        networks.append(current)

    for net in networks:
        net.setdefault("ssid", "<hidden>")
        net.setdefault("bssid", "??:??:??:??:??:??")
        net.setdefault("channel", 0)
        net.setdefault("band", "2.4 GHz")
        net.setdefault("rssi", -100)
        net.setdefault("encrypted", False)
        net.setdefault("security", "Open" if not net.get("encrypted") else "WEP/WPA")

    return sorted(networks, key=lambda x: x["rssi"], reverse=True)


def _rssi_to_quality(rssi: int) -> int:
    """Convert RSSI (dBm) to 0–100 quality score."""
    if rssi >= -50:
        return 100
    if rssi <= -100:
        return 0
    return 2 * (rssi + 100)


def _rssi_label(rssi: int) -> str:
    if rssi >= -60:
        return "Excellent"
    if rssi >= -70:
        return "Good"
    if rssi >= -80:
        return "Fair"
    return "Poor"


# ── Public API ───────────────────────────────────────────────────────────────

def scan_once() -> tuple[list[dict], str]:
    """Trigger one iwlist scan. Returns (networks, error_string)."""
    global _last_scan_time, _scan_error

    try:
        result = subprocess.run(
            ["sudo", "iwlist", WIFI_INTERFACE, "scan"],
            capture_output=True, text=True, timeout=15
        )
        raw = result.stdout
        if not raw.strip():
            err = result.stderr.strip() or "No scan output"
            return [], err

        networks = _parse_iwlist(raw)

        # Enrich with quality metadata
        for net in networks:
            net["quality"] = _rssi_to_quality(net["rssi"])
            net["quality_label"] = _rssi_label(net["rssi"])

        _last_scan_time = time.time()
        _scan_error = ""
        return networks, ""

    except subprocess.TimeoutExpired:
        err = "Scan timed out"
        return [], err
    except Exception as e:
        err = str(e)
        return [], err


def get_networks() -> list[dict]:
    with _lock:
        return list(_networks)


def get_history(ssid: str) -> list[dict]:
    """Return timestamped RSSI history for a given SSID."""
    with _lock:
        return list(_history.get(ssid, []))


def get_all_ssids() -> list[str]:
    with _lock:
        return sorted(_history.keys())


def get_scan_meta() -> dict:
    with _lock:
        return {
            "last_scan": _last_scan_time,
            "error": _scan_error,
            "count": len(_networks),
        }


def get_channel_usage() -> list[dict]:
    """Summarise network count and avg RSSI per channel."""
    with _lock:
        channels: dict[int, list[int]] = defaultdict(list)
        for net in _networks:
            channels[net["channel"]].append(net["rssi"])

    usage = []
    for ch in sorted(channels):
        rssi_vals = channels[ch]
        usage.append({
            "channel": ch,
            "count": len(rssi_vals),
            "avg_rssi": round(sum(rssi_vals) / len(rssi_vals), 1),
        })
    return usage


# ── Background scan loop ─────────────────────────────────────────────────────

def _scan_loop():
    global _networks, _scan_error
    while True:
        nets, err = scan_once()
        ts = time.time()
        with _lock:
            if nets:
                _networks = nets
                for net in nets:
                    _history[net["ssid"]].append({"t": ts, "rssi": net["rssi"]})
            _scan_error = err
        time.sleep(SCAN_INTERVAL_SECONDS)


def start_background_scanner():
    t = threading.Thread(target=_scan_loop, daemon=True)
    t.start()
