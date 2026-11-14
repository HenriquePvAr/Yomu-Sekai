from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import asyncio
import base64
import hashlib
import re
from pathlib import Path

import komyst.ui.app as app_ui

ROOT = Path(__file__).resolve().parents[1]


def _serve(body: bytes, ctype: bytes = b"text/html; charset=utf-8", chunks: int = 1):
    messages = []

    async def inner(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", ctype)]})
        step = max(1, len(body) // chunks)
        parts = [body[i:i + step] for i in range(0, len(body), step)] or [b""]
        for i, part in enumerate(parts):
            await send({"type": "http.response.body", "body": part, "more_body": i < len(parts) - 1})

    async def send(message):
        messages.append(message)

    asyncio.run(app_ui.SecurityHeadersMiddleware(inner)({"type": "http", "path": "/"}, None, send))
    headers = {k.lower(): v for k, v in messages[0]["headers"]}
    csp = headers[b"content-security-policy"].decode("latin-1")
    return csp, b"".join(m.get("body", b"") for m in messages[1:])


def _directive(csp: str, name: str) -> list[str]:
    return next(p for p in csp.split(";") if p.strip().startswith(name + " ")).split()[1:]


def test_csp_script_src_has_no_unsafe_inline_and_img_src_is_not_any_https():
    csp, _ = _serve(b"<html></html>")
    assert "'unsafe-inline'" not in _directive(csp, "script-src")
    img = _directive(csp, "img-src")
    assert "https:" not in img and "*" not in img


def test_inline_scripts_are_allowed_by_hash_only():
    inline = b"window.x = 1;"
    body = b"<script>" + inline + b"</script><script src='/static/a.js'></script><p onclick='x()'>"
    csp, echoed = _serve(body, chunks=3)
    assert echoed == body
    digest = base64.b64encode(hashlib.sha256(inline).digest()).decode()
    script_src = _directive(csp, "script-src")
    assert f"'sha256-{digest}'" in script_src
    assert "'unsafe-inline'" not in script_src and len(script_src) == 2


def test_non_html_response_gets_plain_csp():
    csp, _ = _serve(b"{}", ctype=b"application/json")
    assert _directive(csp, "script-src") == ["'self'"]


def test_shipped_pages_have_no_inline_event_handlers():
    for rel in ("ui/ui_shell.html", "ui/auth_callback.html"):
        html = (ROOT / rel).read_text(encoding="utf-8")
        markup = re.sub(r"<script.*?</script>", "", html, flags=re.S | re.I)
        assert not re.search(r"<[a-z][^>]*\son[a-z]+\s*=", markup, re.I), rel


def test_auth_callback_inline_scripts_are_covered_by_hashes():
    html = (ROOT / "ui" / "auth_callback.html").read_bytes()
    csp, _ = _serve(html)
    assert len(_directive(csp, "script-src")) >= 3


import shutil
import subprocess

import pytest

UI_JS = (ROOT / "static" / "komyst_ui.js").read_text(encoding="utf-8")


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_escape_html_escapes_quotes_and_is_used_for_attributes():
    block = re.search(r"const escapeHtml = .*?\n\s*const escapeAttr = escapeHtml;", UI_JS, re.S).group(0)
    script = block + " console.log(JSON.stringify([escapeHtml(process.argv[1]), escapeAttr(null), escapeHtml(3)]));"
    payload = '<a href="x" onclick=' + "'y'" + '>&'
    out = subprocess.run(["node", "-e", script, "--", payload], capture_output=True, text=True, check=True).stdout
    assert out.strip() == '["&lt;a href=&quot;x&quot; onclick=&#39;y&#39;&gt;&amp;","","3"]'


def test_internal_values_are_escaped_in_templates():
    assert "${escapeHtml(runStatusLabels[item.status] || item.status)}" in UI_JS
    assert "${escapeHtml(result.candidate_count)}" in UI_JS
    assert "${escapeAttr(region)}\"></figure>" in UI_JS
    assert "escapeHtml(listing.reviewable_regions || 0)" in UI_JS


def test_ad_iframe_is_sandboxed_without_same_origin_or_top_navigation():
    src = (ROOT / "static" / "passive_ad_slot.js").read_text(encoding="utf-8")
    flags = re.search(r"setAttribute\('sandbox', '([^']+)'\)", src).group(1).split()
    assert flags == ["allow-scripts", "allow-popups", "allow-popups-to-escape-sandbox"]


def test_comment_body_is_stored_raw_and_every_display_escapes_it():
    src = (ROOT / "komyst" / "community" / "community_store.py").read_text(encoding="utf-8")
    assert "html.escape" not in src
    # the only renderer of this store's comments interpolates through escapeHtml
    render = re.search(r"function renderCommunityComment.*?\n  }\n", UI_JS, re.S).group(0)
    assert "escapeHtml(body)" in render and "${body}" not in render.replace("escapeHtml(body)", "")
