"""Isolated pywebview harness; never starts the installed Komyst executable."""
import webview
import os
from pathlib import Path
import threading
import time
from urllib.request import urlopen

os.environ.setdefault("KOMYST_UI_PORT", "8181")
import komyst.ui.app as app_ui

from komyst.desktop.app import DesktopApi


webview.create_window(
    "Komyst local-media harness",
    "http://127.0.0.1:8181/",
    js_api=DesktopApi(),
    width=1280,
    height=900,
)
harness_profile = Path(os.getenv("TEMP", ".")) / "komyst-pywebview-harness-profile"
harness_profile.mkdir(parents=True, exist_ok=True)
threading.Thread(target=app_ui.main, name="isolated-ui-server", daemon=True).start()
for _ in range(60):
    try:
        with urlopen("http://127.0.0.1:8181/api/health", timeout=1):
            break
    except Exception:
        time.sleep(0.25)
webview.start(private_mode=False, storage_path=str(harness_profile))
