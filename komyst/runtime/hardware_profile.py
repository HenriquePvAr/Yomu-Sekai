"""Hardware profiles (leve / equilibrado / qualidade).

The profile only supplies *defaults*: an environment variable that is already set (process
environment or ``.env.local``) always wins.  It is applied to ``os.environ`` before
``komyst.config.settings`` reads it, so every consumer (and child process) sees one value.
Detection never raises: unknown RAM/GPU degrades to the most conservative profile.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from typing import Any, Mapping, MutableMapping

PROFILES = ("leve", "equilibrado", "qualidade")
STATE_ENV = "KOMYST_HARDWARE_PROFILE_STATE"

# Only the keys a profile changes. GENERATIVE_INPAINT_ENABLED (FLUX) is never set by a profile;
# "auto" workers = leave PIPELINE_PAGE_WORKERS to the existing auto policy.
PROFILE_VALUES: dict[str, dict[str, str]] = {
    "leve": {"PIPELINE_PAGE_WORKERS": "1", "OCR_RESIDUAL_SWEEP_MODE": "off",
             "CLEAN_COMPARE_FILLS": "0", "ADVANCED_ART_INPAINTING": "1"},
    "equilibrado": {"PIPELINE_PAGE_WORKERS": "2", "OCR_RESIDUAL_SWEEP_MODE": "always",
                    "CLEAN_COMPARE_FILLS": "1", "ADVANCED_ART_INPAINTING": "1"},
    "qualidade": {"OCR_RESIDUAL_SWEEP_MODE": "always",
                  "CLEAN_COMPARE_FILLS": "1", "ADVANCED_ART_INPAINTING": "1"},
}
_NOT_DEDICATED = re.compile(r"intel|basic|remote|virtual|parsec|vmware|hyper-v|citrix", re.I)


def _vram_gb() -> float | None:
    """Largest dedicated-GPU VRAM in GB. nvidia-smi first (Win32 AdapterRAM caps at 4 GB)."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5, check=False).stdout
        values = [float(x) for x in out.split() if x.replace(".", "", 1).isdigit()]
        if values:
            return round(max(values) / 1024, 2)
    except Exception:  # noqa: BLE001 - no NVIDIA driver: try the generic query
        pass
    try:  # AMD/Intel: 64-bit size from the display-class registry (AdapterRAM caps at 4 GB)
        import winreg

        key = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
        sizes = []
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key) as root:
            for i in range(winreg.QueryInfoKey(root)[0]):
                try:
                    with winreg.OpenKey(root, winreg.EnumKey(root, i)) as sub:
                        name = str(winreg.QueryValueEx(sub, "DriverDesc")[0])
                        size = int(winreg.QueryValueEx(sub, "HardwareInformation.qwMemorySize")[0])
                except OSError:
                    continue
                if not _NOT_DEDICATED.search(name):
                    sizes.append(size)
        if sizes:
            return round(max(sizes) / 1024 ** 3, 2)
    except Exception:  # noqa: BLE001 - not Windows / key missing: fall back to WMI
        pass
    try:
        from komyst.runtime.resource_monitor import detect_gpu_basic

        sizes = [d["adapter_ram_mb"] for d in detect_gpu_basic().get("devices", [])
                 if d.get("adapter_ram_mb") and not _NOT_DEDICATED.search(d.get("name", ""))]
        return round(max(sizes) / 1024, 2) if sizes else None
    except Exception:  # noqa: BLE001
        return None


def detect() -> dict[str, Any]:
    """RAM (total/free, GB) and dedicated-GPU VRAM (GB); ``None`` for anything unmeasured."""
    ram_total = ram_free = None
    try:
        import psutil

        mem = psutil.virtual_memory()
        ram_total, ram_free = round(mem.total / 1024 ** 3, 2), round(mem.available / 1024 ** 3, 2)
    except Exception:  # noqa: BLE001 - no psutil
        pass
    return {"ram_total_gb": ram_total, "ram_free_gb": ram_free, "gpu_vram_gb": _vram_gb()}


def select_profile(detected: Mapping[str, Any], override: str = "auto") -> str:
    """Profile for ``detected``; a valid manual ``override`` wins, unknown values count as auto."""
    forced = str(override or "auto").strip().lower()
    if forced in PROFILES:
        return forced
    ram, vram = detected.get("ram_total_gb"), detected.get("gpu_vram_gb")
    if ram is None or vram is None:
        return "leve"
    if ram >= 24 and vram >= 7.5:  # an 8 GB card reports ~7.98 GiB
        return "qualidade"
    if ram >= 12 and vram >= 3.5:  # a 4 GB card reports ~3.99 GiB
        return "equilibrado"
    return "leve"


def resolve(env: Mapping[str, str] | None = None, detected: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Pick the profile and split its values into ``applied`` and ``overridden_by_env``."""
    env = os.environ if env is None else env
    raw = str(env.get("HARDWARE_PROFILE") or "auto").strip().lower()
    manual = raw in PROFILES
    det = dict(detect() if detected is None and not manual else (detected or {}))
    profile = select_profile(det, raw)
    if manual:
        reason = f"HARDWARE_PROFILE={profile} (manual)"
    else:
        reason = (f"auto: ram_total_gb={det.get('ram_total_gb')} gpu_vram_gb={det.get('gpu_vram_gb')}"
                  + ("" if raw == "auto" else f" (invalid HARDWARE_PROFILE={raw!r} ignored)"))
    applied, overridden = {}, {}
    for key, value in PROFILE_VALUES[profile].items():
        if str(env.get(key) or "") != "":
            overridden[key] = env[key]
        else:
            applied[key] = value
    return {"profile": profile, "reason": reason, "detected": det,
            "applied": applied, "overridden_by_env": overridden}


def apply_to_environ(env: MutableMapping[str, str] | None = None) -> dict[str, Any]:
    """Resolve once per process tree and write the profile defaults into ``env``."""
    env = os.environ if env is None else env
    cached = env.get(STATE_ENV)
    if cached:
        try:
            return json.loads(cached)
        except ValueError:
            pass
    if env.get("KOMYST_HERMETIC_TEST_ENV") and str(env.get("HARDWARE_PROFILE") or "auto").lower() == "auto":
        return {"profile": "none", "reason": "hermetic test environment", "applied": {}}
    state = resolve(env)
    env.update(state["applied"])
    env[STATE_ENV] = json.dumps(state)
    return state


def state() -> dict[str, Any]:
    """Profile state of this process (for the timing report and job log)."""
    try:
        return json.loads(os.environ.get(STATE_ENV) or "{}") or {"profile": "none"}
    except ValueError:
        return {"profile": "none"}
