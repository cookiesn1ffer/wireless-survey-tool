# >\_ Wireless Survey Tool

> Network diagnostics and wireless survey tool for Raspberry Pi Zero WH.

![Screenshot](screenshot.png)

---

## What it does

A lightweight Flask web server that runs on a Raspberry Pi Zero WH and exposes a browser-based dashboard for wireless network diagnostics and survey data.

| Feature            | Details                                        |
| ------------------ | ---------------------------------------------- |
| Network scan       | Detect nearby SSIDs, signal strength, channel  |
| Device diagnostics | Interface stats, IP info, link quality         |
| Web dashboard      | Access from any device on the same network     |
| Portable           | Runs headless on Pi Zero WH, no monitor needed |

---

## Requirements

- Raspberry Pi Zero WH
- Python 3.10+
- Linux (Raspbian/Raspberry Pi OS)

## Installation

```bash
git clone https://github.com/cookiesn1ffer/wireless-survey-tool.git
cd wireless-survey-tool
pip install -r requirements.txt
python app.py
```

Open http://<pi-ip>:5000 in your browser.

---

## Stack

- **Flask** — web dashboard
- **Python** — network diagnostics

---

## License

Copyright (c) 2026 Aarush (cookiesn1ffer). All rights reserved.
This software is proprietary. See LICENSE for details.
