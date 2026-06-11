"""
Wireless Survey Tool — Flask entry point
"""

import csv
import json
import os
import threading
import time
from datetime import datetime
from flask import Flask, jsonify, render_template, request

from config import HOST, PORT, DEBUG, LOG_DIR
from scanner.wifi import (
    start_background_scanner,
    get_networks,
    get_history,
    get_all_ssids,
    get_scan_meta,
    get_channel_usage,
)
from scanner.diagnostics import (
    ping,
    traceroute,
    dns_lookup,
    speedtest,
    interface_info,
    format_bytes,
)

app = Flask(__name__)

# Active speedtest state (runs in background thread)
_speedtest_state = {"running": False, "result": None, "started": None}
_speedtest_lock = threading.Lock()

os.makedirs(LOG_DIR, exist_ok=True)


# ── Page routes ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/scanner")
def scanner_page():
    return render_template("scanner.html")


@app.route("/diagnostics")
def diagnostics_page():
    return render_template("diagnostics.html")


@app.route("/history")
def history_page():
    ssids = get_all_ssids()
    return render_template("history.html", ssids=ssids)


# ── API — scanner ─────────────────────────────────────────────────────────────

@app.route("/api/networks")
def api_networks():
    return jsonify(get_networks())


@app.route("/api/scan/meta")
def api_scan_meta():
    meta = get_scan_meta()
    meta["last_scan_fmt"] = (
        datetime.fromtimestamp(meta["last_scan"]).strftime("%H:%M:%S")
        if meta["last_scan"] else "Never"
    )
    return jsonify(meta)


@app.route("/api/channels")
def api_channels():
    return jsonify(get_channel_usage())


@app.route("/api/history/<path:ssid>")
def api_history(ssid):
    raw = get_history(ssid)
    points = [{"t": round(p["t"] * 1000), "rssi": p["rssi"]} for p in raw]
    return jsonify(points)


@app.route("/api/export/csv")
def api_export_csv():
    networks = get_networks()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(LOG_DIR, f"scan_{ts}.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["ssid", "bssid", "channel", "band", "rssi", "quality", "security"]
        )
        writer.writeheader()
        writer.writerows(networks)
    return jsonify({"file": path, "count": len(networks)})


# ── API — diagnostics ─────────────────────────────────────────────────────────

@app.route("/api/ping")
def api_ping():
    host = request.args.get("host", "8.8.8.8")
    count = int(request.args.get("count", 4))
    return jsonify(ping(host, count))


@app.route("/api/traceroute")
def api_traceroute():
    host = request.args.get("host", "8.8.8.8")
    return jsonify(traceroute(host))


@app.route("/api/dns")
def api_dns():
    hostname = request.args.get("host", "google.com")
    return jsonify(dns_lookup(hostname))


@app.route("/api/interface")
def api_interface():
    info = interface_info()
    info["rx_fmt"] = format_bytes(info.get("rx_bytes", 0))
    info["tx_fmt"] = format_bytes(info.get("tx_bytes", 0))
    return jsonify(info)


@app.route("/api/speedtest/start", methods=["POST"])
def api_speedtest_start():
    with _speedtest_lock:
        if _speedtest_state["running"]:
            return jsonify({"error": "Speedtest already running"}), 409
        _speedtest_state["running"] = True
        _speedtest_state["result"] = None
        _speedtest_state["started"] = time.time()

    def run():
        result = speedtest()
        with _speedtest_lock:
            _speedtest_state["result"] = result
            _speedtest_state["running"] = False

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"status": "started"})


@app.route("/api/speedtest/status")
def api_speedtest_status():
    with _speedtest_lock:
        return jsonify({
            "running": _speedtest_state["running"],
            "result": _speedtest_state["result"],
            "elapsed": (
                round(time.time() - _speedtest_state["started"], 1)
                if _speedtest_state["started"] else None
            ),
        })


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    start_background_scanner()
    app.run(host=HOST, port=PORT, debug=DEBUG)
