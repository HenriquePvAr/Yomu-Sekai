"""Public home-page previews, refreshed on demand with an isolated browser."""

import base64
import io
import threading
import time

SUPPORTED_SOURCE_URLS = {
    "webtoon": "https://www.webtoons.com/en/",
    "comix": "https://comix.to/browse?genres_in=101137",
    "vortex": "https://vortexscans.org/",
}
REFRESH_SECONDS = 60
# defer: three public sources per local server, use a shared cache if hosting multiple servers.
_cache = {}
_cache_lock = threading.Lock()
_browser_lock = threading.Lock()


def _capture(key):
    from PIL import Image
    from selenium.webdriver.support.ui import WebDriverWait
    from yomu.download.down import (
        _create_driver, _set_browser_timeouts, _capture_driver_ownership,
        _bounded_driver_teardown,
    )

    # Never attach to the operator's browser or reuse authenticated source profiles.
    with _browser_lock:
        driver = _create_driver()
        ownership = _capture_driver_ownership(driver)
        try:
            _set_browser_timeouts(driver, 20)
            driver.set_window_size(1280, 800)
            driver.get(SUPPORTED_SOURCE_URLS[key])
            WebDriverWait(driver, 10).until(lambda d: d.execute_script(
                "return document.readyState === 'complete' && "
                "Array.from(document.images).some(i => i.complete && i.naturalWidth > 100)"
            ))
            if any(word in driver.title.lower() for word in (
                "just a moment", "verify you are human", "access denied",
            )):
                raise RuntimeError("source_preview_unavailable")
            image = Image.open(io.BytesIO(driver.get_screenshot_as_png())).convert("RGB")
            image.thumbnail((800, 500))
            output = io.BytesIO()
            image.save(output, "JPEG", quality=80)
            return "data:image/jpeg;base64," + base64.b64encode(output.getvalue()).decode("ascii")
        finally:
            _bounded_driver_teardown(driver, ownership, timeout_seconds=3, cleanup_timeout_seconds=2)


def _refresh(key):
    try:
        preview = _capture(key)
        with _cache_lock:
            _cache[key].update(image=preview, captured_at=time.time(), error=False)
    except Exception:
        # A failed refresh keeps the last good preview and its original timestamp.
        with _cache_lock:
            _cache[key]["error"] = True
    finally:
        with _cache_lock:
            _cache[key].update(refreshing=False, checked_at=time.monotonic())


def source_preview(key):
    if key not in SUPPORTED_SOURCE_URLS:
        raise ValueError("unsupported_source")
    with _cache_lock:
        entry = _cache.setdefault(key, {
            "image": "", "captured_at": None, "checked_at": None,
            "refreshing": False, "error": False,
        })
        if not entry["refreshing"] and (
            entry["checked_at"] is None or time.monotonic() - entry["checked_at"] >= REFRESH_SECONDS
        ):
            entry["refreshing"] = True
            threading.Thread(target=_refresh, args=(key,), daemon=True,
                             name=f"source-preview-{key}").start()
        return {field: entry[field] for field in ("image", "captured_at", "refreshing", "error")}
