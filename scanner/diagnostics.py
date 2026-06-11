"""
Network diagnostics — ping, traceroute, DNS, speedtest, interface info.
"""

import re
import socket
import subprocess
import time
from config import WIFI_INTERFACE


# ── Ping ─────────────────────────────────────────────────────────────────────

def ping(host: str = "8.8.8.8", count: int = 4) -> dict:
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", "2", host],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout

        # Parse summary line: "4 packets transmitted, 4 received, 0% packet loss"
        m = re.search(
            r"(\d+) packets transmitted, (\d+) received.*?(\d+(?:\.\d+)?)% packet loss",
            output
        )
        sent = int(m.group(1)) if m else count
        recv = int(m.group(2)) if m else 0
        loss = float(m.group(3)) if m else 100.0

        # Parse rtt: "rtt min/avg/max/mdev = 1.2/2.3/4.5/0.6 ms"
        rtt_m = re.search(r"rtt .* = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms", output)
        rtt_min = float(rtt_m.group(1)) if rtt_m else None
        rtt_avg = float(rtt_m.group(2)) if rtt_m else None
        rtt_max = float(rtt_m.group(3)) if rtt_m else None

        return {
            "host": host,
            "sent": sent,
            "received": recv,
            "loss_pct": loss,
            "rtt_min": rtt_min,
            "rtt_avg": rtt_avg,
            "rtt_max": rtt_max,
            "success": recv > 0,
            "raw": output,
        }
    except Exception as e:
        return {"host": host, "success": False, "error": str(e)}


# ── Traceroute ───────────────────────────────────────────────────────────────

def traceroute(host: str = "8.8.8.8", max_hops: int = 20) -> dict:
    try:
        result = subprocess.run(
            ["traceroute", "-n", "-m", str(max_hops), "-w", "2", host],
            capture_output=True, text=True, timeout=60
        )
        hops = []
        for line in result.stdout.splitlines()[1:]:
            parts = line.split()
            if not parts:
                continue
            try:
                hop_num = int(parts[0])
            except ValueError:
                continue

            if parts[1] == "*":
                hops.append({"hop": hop_num, "ip": "*", "rtt": None})
            else:
                ip = parts[1]
                rtts = [float(p) for p in parts[2:] if re.match(r"^\d+\.\d+$", p)]
                avg = round(sum(rtts) / len(rtts), 2) if rtts else None
                hops.append({"hop": hop_num, "ip": ip, "rtt": avg})

        return {"host": host, "hops": hops, "success": True, "raw": result.stdout}
    except Exception as e:
        return {"host": host, "hops": [], "success": False, "error": str(e)}


# ── DNS lookup ───────────────────────────────────────────────────────────────

def dns_lookup(hostname: str) -> dict:
    try:
        start = time.time()
        addrs = socket.getaddrinfo(hostname, None)
        elapsed = round((time.time() - start) * 1000, 2)
        ips = list({a[4][0] for a in addrs})
        return {"hostname": hostname, "ips": ips, "elapsed_ms": elapsed, "success": True}
    except Exception as e:
        return {"hostname": hostname, "ips": [], "success": False, "error": str(e)}


# ── Speedtest ────────────────────────────────────────────────────────────────

def speedtest() -> dict:
    """Run speedtest-cli. Can take 20–60 s on Pi Zero — run in a thread."""
    try:
        result = subprocess.run(
            ["speedtest-cli", "--simple"],
            capture_output=True, text=True, timeout=120
        )
        lines = result.stdout.strip().splitlines()
        data = {}
        for line in lines:
            if line.startswith("Ping:"):
                m = re.search(r"([\d.]+)\s*ms", line)
                data["ping_ms"] = float(m.group(1)) if m else None
            elif line.startswith("Download:"):
                m = re.search(r"([\d.]+)\s*Mbit/s", line)
                data["download_mbps"] = float(m.group(1)) if m else None
            elif line.startswith("Upload:"):
                m = re.search(r"([\d.]+)\s*Mbit/s", line)
                data["upload_mbps"] = float(m.group(1)) if m else None
        data["success"] = "download_mbps" in data
        return data
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Speedtest timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Interface info ────────────────────────────────────────────────────────────

def interface_info() -> dict:
    """Get IP, gateway, DNS, TX/RX bytes for WIFI_INTERFACE."""
    info = {"interface": WIFI_INTERFACE}

    # IP address
    try:
        result = subprocess.run(
            ["ip", "addr", "show", WIFI_INTERFACE],
            capture_output=True, text=True
        )
        m = re.search(r"inet\s+([\d.]+/\d+)", result.stdout)
        info["ip"] = m.group(1) if m else "N/A"
    except Exception:
        info["ip"] = "N/A"

    # Default gateway
    try:
        result = subprocess.run(["ip", "route"], capture_output=True, text=True)
        m = re.search(r"default via ([\d.]+)", result.stdout)
        info["gateway"] = m.group(1) if m else "N/A"
    except Exception:
        info["gateway"] = "N/A"

    # DNS servers
    try:
        with open("/etc/resolv.conf") as f:
            dns = re.findall(r"^nameserver\s+([\d.]+)", f.read(), re.MULTILINE)
        info["dns"] = dns if dns else ["N/A"]
    except Exception:
        info["dns"] = ["N/A"]

    # TX/RX bytes
    try:
        with open(f"/sys/class/net/{WIFI_INTERFACE}/statistics/rx_bytes") as f:
            info["rx_bytes"] = int(f.read().strip())
        with open(f"/sys/class/net/{WIFI_INTERFACE}/statistics/tx_bytes") as f:
            info["tx_bytes"] = int(f.read().strip())
    except Exception:
        info["rx_bytes"] = 0
        info["tx_bytes"] = 0

    # Link speed (may not be available on all adapters)
    try:
        result = subprocess.run(
            ["iwconfig", WIFI_INTERFACE], capture_output=True, text=True
        )
        m = re.search(r"Bit Rate=([\d.]+)\s*Mb/s", result.stdout)
        info["link_speed_mbps"] = float(m.group(1)) if m else None

        m2 = re.search(r'ESSID:"(.*?)"', result.stdout)
        info["connected_ssid"] = m2.group(1) if m2 else "N/A"
    except Exception:
        info["link_speed_mbps"] = None
        info["connected_ssid"] = "N/A"

    return info


def format_bytes(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"
