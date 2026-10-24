"""Local integrity checks for the private Drive ↔ Colab research workflow.

This helper never contacts Drive, Colab, or a model provider. The connected
Google Drive MCP performs the transfer; this script validates the local bytes
before upload and validates a downloaded result folder after retrieval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import stat
import struct
import zipfile
import zlib
from pathlib import Path, PurePosixPath


EXPECTED_INPUT_SHA256 = "725c75c2846e2e73eadd3a2d2f661b3e59ff8db996bd849d712dd0a710ddf427"
EXPECTED_SOURCE_SHA256 = "da5714748b63216fba3980ec6bf224d4223c56b8d51f00a595debbe8c6510b24"
EXPECTED_DIMENSIONS = (795, 960)
REQUIRED_INPUTS = {
    "source.png",
    "mask_report.json",
    "mask_speech.png",
    "mask_full_experimental.png",
    "mask_sfx.png",
    "mask_scenarios_preview.png",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_candidate_archive(path: Path) -> dict[str, object]:
    """Inspect an image-only candidate ZIP without extracting or executing it."""
    path = path.resolve(strict=True)
    archive_sha = sha256_file(path)
    candidates: list[dict[str, object]] = []
    seen_names: set[str] = set()
    total_size = 0

    with zipfile.ZipFile(path) as archive:
        entries = [entry for entry in archive.infolist() if not entry.is_dir()]
        if not entries or len(entries) > 32:
            raise ValueError("Candidate archive must contain between 1 and 32 files")
        for entry in entries:
            if not _safe_archive_name(entry.filename):
                raise ValueError(f"Unsafe archive path: {entry.filename!r}")
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError(f"Archive symlink rejected: {entry.filename!r}")
            normalized_name = entry.filename.casefold()
            if normalized_name in seen_names:
                raise ValueError(f"Duplicate archive path: {entry.filename!r}")
            seen_names.add(normalized_name)
            if PurePosixPath(entry.filename).suffix.lower() != ".png":
                raise ValueError(f"Only PNG candidates are accepted: {entry.filename!r}")
            if entry.file_size > 25 * 1024 * 1024:
                raise ValueError(f"Candidate exceeds 25 MiB: {entry.filename!r}")
            total_size += entry.file_size
            if total_size > 100 * 1024 * 1024:
                raise ValueError("Candidate archive expands beyond 100 MiB")

        if archive.testzip() is not None:
            raise ValueError("Candidate ZIP CRC validation failed")

        for entry in entries:
            digest = hashlib.sha256()
            with archive.open(entry) as stream:
                header = stream.read(33)
                if (
                    len(header) != 33
                    or header[:8] != b"\x89PNG\r\n\x1a\n"
                    or struct.unpack(">I", header[8:12])[0] != 13
                    or header[12:16] != b"IHDR"
                ):
                    raise ValueError(f"Invalid PNG IHDR: {entry.filename!r}")
                expected_crc = struct.unpack(">I", header[29:33])[0]
                if zlib.crc32(header[12:29]) & 0xFFFFFFFF != expected_crc:
                    raise ValueError(f"Invalid PNG IHDR CRC: {entry.filename!r}")
                width, height = struct.unpack(">II", header[16:24])
                if not (64 <= width <= 8192 and 64 <= height <= 8192):
                    raise ValueError(f"Unexpected PNG dimensions: {entry.filename!r}")
                digest.update(header)
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            candidates.append(
                {
                    "name": entry.filename,
                    "size_bytes": entry.file_size,
                    "sha256": digest.hexdigest(),
                    "dimensions": [width, height],
                }
            )

    return {
        "status": "PASS_MASKS_REQUIRED",
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": archive_sha,
        "candidate_count": len(candidates),
        "masks_present": False,
        "candidates": candidates,
    }


def _safe_archive_name(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and "\\" not in name
        and ":" not in name
    )


def inspect_input(path: Path) -> dict[str, object]:
    path = path.resolve(strict=True)
    archive_sha = sha256_file(path)
    if archive_sha != EXPECTED_INPUT_SHA256:
        raise ValueError("Input ZIP SHA-256 does not match the reviewed bundle")

    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names: set[str] = set()
        expanded_size = 0
        for entry in entries:
            if not _safe_archive_name(entry.filename):
                raise ValueError(f"Unsafe archive path: {entry.filename!r}")
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError(f"Archive symlink rejected: {entry.filename!r}")
            names.add(entry.filename)
            expanded_size += entry.file_size
        if expanded_size > 15 * 1024 * 1024:
            raise ValueError("Unexpected expanded input size")
        if archive.testzip() is not None:
            raise ValueError("Input ZIP CRC validation failed")
        missing = sorted(REQUIRED_INPUTS - names)
        if missing:
            raise ValueError(f"Required input artifacts missing: {missing}")
        report = json.loads(archive.read("mask_report.json"))
        source = archive.read("source.png")

    if hashlib.sha256(source).hexdigest() != EXPECTED_SOURCE_SHA256:
        raise ValueError("Source image SHA-256 mismatch")
    if report.get("source_sha256") != EXPECTED_SOURCE_SHA256:
        raise ValueError("Mask report is not bound to the expected source")
    if len(source) < 24 or source[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Source is not a valid PNG")
    dimensions = struct.unpack(">II", source[16:24])
    if dimensions != EXPECTED_DIMENSIONS:
        raise ValueError(f"Unexpected source dimensions: {dimensions}")
    return {
        "status": "PASS",
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": archive_sha,
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "dimensions": list(dimensions),
        "required_artifacts": sorted(REQUIRED_INPUTS),
    }


def verify_result_folder(folder: Path) -> dict[str, object]:
    folder = folder.resolve(strict=True)
    manifest_path = folder / "artifact_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError("Artifact manifest has no artifact entries")

    verified: list[str] = []
    for name, expected in artifacts.items():
        if not isinstance(name, str) or not _safe_archive_name(name):
            raise ValueError(f"Unsafe artifact path in manifest: {name!r}")
        artifact = (folder / name).resolve(strict=True)
        if artifact.parent != folder:
            raise ValueError(f"Artifact escaped result folder: {name!r}")
        if artifact.stat().st_size != expected.get("size"):
            raise ValueError(f"Artifact size mismatch: {name}")
        if sha256_file(artifact) != expected.get("sha256"):
            raise ValueError(f"Artifact SHA-256 mismatch: {name}")
        verified.append(name)
    return {
        "status": "PASS",
        "folder": str(folder),
        "run_id": manifest.get("run_id"),
        "source_sha256": manifest.get("source_sha256"),
        "checkpoint_sha256": manifest.get("checkpoint_sha256"),
        "artifacts_verified": sorted(verified),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    input_parser = subparsers.add_parser("inspect-input", help="verify the approved input ZIP")
    input_parser.add_argument("zip", type=Path)
    candidates_parser = subparsers.add_parser(
        "inspect-candidates", help="verify an image-only candidate ZIP without extraction"
    )
    candidates_parser.add_argument("zip", type=Path)
    results_parser = subparsers.add_parser("verify-results", help="verify a downloaded Colab result folder")
    results_parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    if args.command == "inspect-input":
        result = inspect_input(args.zip)
    elif args.command == "inspect-candidates":
        result = inspect_candidate_archive(args.zip)
    else:
        result = verify_result_folder(args.folder)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
