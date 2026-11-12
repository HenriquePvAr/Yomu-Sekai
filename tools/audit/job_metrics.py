#!/usr/bin/env python3
"""Read-only metrics extractor for one Komyst job output directory.

This utility intentionally uses only the Python standard library and never
imports the application package.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Não foi possível ler {path}: {exc}") from exc
    return value if isinstance(value, dict) else {}


def _walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def _count_pairs(items: list[Any], first: str, second: str) -> dict[str, int]:
    counts = Counter()
    for item in items:
        if not isinstance(item, dict):
            continue
        key = (str(item.get(first) or "<ausente>"), str(item.get(second) or "<ausente>"))
        counts[" | ".join(key)] += 1
    return dict(sorted(counts.items()))


def _count_field(items: list[Any], field: str) -> dict[str, int]:
    counts = Counter(
        str(item.get(field) or "<ausente>")
        for item in items
        if isinstance(item, dict)
    )
    return dict(sorted(counts.items()))


def _directory_bytes(root: Path) -> dict[str, int]:
    totals: Counter[str] = Counter()
    for path in root.rglob("*"):
        try:
            if path.is_symlink() or not path.is_file():
                continue
            relative = path.relative_to(root)
            bucket = relative.parts[0] if len(relative.parts) > 1 else "(raiz)"
            totals[bucket] += path.stat().st_size
        except OSError:
            continue
    return dict(sorted(totals.items()))


def _page_count(root: Path) -> int:
    pages = root / "pages"
    if not pages.is_dir():
        return 0
    pattern = re.compile(r"^page_\d+\.png$", re.IGNORECASE)
    return sum(1 for p in pages.iterdir() if p.is_file() and pattern.fullmatch(p.name))


def _clean_reason_counts(manifest: dict[str, Any]) -> dict[str, int]:
    counts = Counter()
    provenance = manifest.get("provenance", {})
    if isinstance(provenance, dict):
        for page_id, page in provenance.items():
            if not isinstance(page, dict):
                continue
            cert = page.get("clean_certificate", {})
            if isinstance(cert, dict):
                counts[str(cert.get("reason") or "<ausente>")] += 1
            else:
                counts["<ausente>"] += 1
    return dict(sorted(counts.items()))


def _terminal_items(quality: dict[str, Any]) -> list[Any]:
    items: list[Any] = []
    for page in quality.get("pages", []) if isinstance(quality.get("pages", []), list) else []:
        if isinstance(page, dict) and isinstance(page.get("translation_terminal_items"), list):
            items.extend(page["translation_terminal_items"])
    return items


def _resource_monitoring(root: Path, reports: list[dict[str, Any]]) -> Any:
    for report in reports:
        for node in _walk_dicts(report):
            if "resource_monitoring" in node:
                return node["resource_monitoring"]
    for path in root.rglob("*.json"):
        if path.name in {"timing_report.json", "artifact_manifest.json", "quality_report.json"}:
            continue
        try:
            data = _read_json(path)
        except ValueError:
            continue
        for node in _walk_dicts(data):
            if "resource_monitoring" in node:
                return node["resource_monitoring"]
    return None


def collect_metrics(run_dir: str | Path) -> dict[str, Any]:
    root = Path(run_dir).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Pasta de execução não encontrada: {root}")
    timing = _read_json(root / "timing_report.json")
    manifest = _read_json(root / "artifact_manifest.json")
    quality_report = _read_json(root / "quality_report.json")
    quality = quality_report.get("summary", {}).get("quality_validation", {})
    if not isinstance(quality, dict):
        quality = {}
    terminals = _terminal_items(quality_report)
    folder_bytes = _directory_bytes(root)
    total_bytes = sum(folder_bytes.values())
    pages = _page_count(root)
    return {
        "run_dir": str(root),
        "run_id": root.name,
        "total_seconds": timing.get("total_seconds"),
        "stage_seconds": timing.get("stage_seconds", {}),
        "clean_certificate_reason_counts_by_page": _clean_reason_counts(manifest),
        "translation_accounting": quality.get("translation_accounting", {}),
        "severity": quality.get("severity"),
        "reason_codes": quality.get("reason_codes", []),
        "physical_gate_passed": quality.get("physical_gate_passed"),
        "physical_source_residual_count": quality.get("physical_source_residual_count"),
        "translation_terminal_state_reason_counts": _count_pairs(
            terminals, "translation_final_state", "translation_final_reason"
        ),
        "cleanup_fill_source_counts": _count_field(terminals, "cleanup_fill_source"),
        "bytes_by_subfolder": folder_bytes,
        "total_bytes": total_bytes,
        "page_count": pages,
        "megabytes_per_page": round(total_bytes / (1024 * 1024) / pages, 4) if pages else None,
        "resource_monitoring": _resource_monitoring(root, [timing, manifest, quality_report]),
        "inference_devices": timing.get("inference_devices"),
        "runtime_environment": timing.get("runtime_environment"),
    }


def render_table(metrics: dict[str, Any]) -> str:
    rows = [
        ("Execução", metrics["run_id"]),
        ("Tempo total (s)", metrics["total_seconds"]),
        ("Páginas", metrics["page_count"]),
        ("MB/página", metrics["megabytes_per_page"]),
        ("Bytes totais", metrics["total_bytes"]),
        ("Gravidade", metrics["severity"]),
        ("Portão físico", metrics["physical_gate_passed"]),
        ("Resíduos físicos", metrics["physical_source_residual_count"]),
        ("Certificados por motivo", json.dumps(metrics["clean_certificate_reason_counts_by_page"], ensure_ascii=False)),
        ("Estados terminais", json.dumps(metrics["translation_terminal_state_reason_counts"], ensure_ascii=False)),
        ("Fontes de preenchimento", json.dumps(metrics["cleanup_fill_source_counts"], ensure_ascii=False)),
        ("Pastas (bytes)", json.dumps(metrics["bytes_by_subfolder"], ensure_ascii=False)),
        ("Monitor de recursos", json.dumps(metrics["resource_monitoring"], ensure_ascii=False)),
        ("Dispositivos de inferência", json.dumps(metrics["inference_devices"], ensure_ascii=False)),
        ("Ambiente de execução", json.dumps(metrics["runtime_environment"], ensure_ascii=False)),
    ]
    width = max(len(label) for label, _ in rows)
    return "\n".join(f"{label:<{width}} | {value}" for label, value in rows)


def render_comparison(left: dict[str, Any], right: dict[str, Any]) -> str:
    keys = ["total_seconds", "page_count", "megabytes_per_page", "total_bytes", "severity",
            "physical_gate_passed", "physical_source_residual_count"]
    lines = [f"Métrica | {left['run_id']} | {right['run_id']} | diferença (B-A)"]
    lines.append("---|---:|---:|---:")
    for key in keys:
        a, b = left.get(key), right.get(key)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            diff = round(b - a, 4)
        else:
            diff = "—" if a == b else f"{a!s} → {b!s}"
        lines.append(f"{key} | {a} | {b} | {diff}")
    for stage in sorted(set(left.get("stage_seconds", {})) | set(right.get("stage_seconds", {}))):
        a = left.get("stage_seconds", {}).get(stage)
        b = right.get("stage_seconds", {}).get(stage)
        delta = round(b - a, 4) if isinstance(a, (int, float)) and isinstance(b, (int, float)) else "—"
        lines.append(f"stage:{stage} | {a} | {b} | {delta}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", nargs="?", help="pasta de execução")
    parser.add_argument("--compare", nargs=2, metavar=("A", "B"), help="comparar duas execuções")
    parser.add_argument("--json", action="store_true", help="imprimir JSON")
    args = parser.parse_args(argv)
    try:
        if args.compare:
            a, b = (collect_metrics(path) for path in args.compare)
            print(render_comparison(a, b))
        elif args.run_dir:
            result = collect_metrics(args.run_dir)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                print("\n" + render_table(result))
        else:
            parser.error("informe run_dir ou --compare A B")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
