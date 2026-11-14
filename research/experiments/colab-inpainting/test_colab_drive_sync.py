from __future__ import annotations

import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import zlib

from colab_drive_sync import (
    _safe_archive_name,
    inspect_candidate_archive,
    verify_result_folder,
)


def _png_header(width: int = 128, height: int = 96) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    chunk = b"IHDR" + ihdr
    return (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", len(ihdr))
        + chunk
        + struct.pack(">I", zlib.crc32(chunk))
    )


class ColabDriveSyncTests(unittest.TestCase):
    def test_archive_path_safety(self) -> None:
        self.assertTrue(_safe_archive_name("results/report.json"))
        self.assertFalse(_safe_archive_name("../secret"))
        self.assertFalse(_safe_archive_name("C:/secret"))
        self.assertFalse(_safe_archive_name("folder\\secret"))

    def test_candidate_archive_reports_missing_masks_without_extracting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "candidates.zip"
            with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
                archive.writestr("01_phrase.png", _png_header())
            result = inspect_candidate_archive(archive_path)
            self.assertEqual(result["status"], "PASS_MASKS_REQUIRED")
            self.assertEqual(result["candidate_count"], 1)
            self.assertFalse(result["masks_present"])
            self.assertEqual(result["candidates"][0]["dimensions"], [128, 96])

    def test_candidate_archive_rejects_non_png_and_path_traversal(self) -> None:
        for filename in ("candidate.jpg", "../candidate.png"):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as tmp:
                archive_path = Path(tmp) / "candidates.zip"
                with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
                    archive.writestr(filename, _png_header())
                with self.assertRaises(ValueError):
                    inspect_candidate_archive(archive_path)

    def test_candidate_archive_rejects_invalid_png_header_crc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "candidates.zip"
            invalid = _png_header()[:-1] + b"\x00"
            with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
                archive.writestr("candidate.png", invalid)
            with self.assertRaisesRegex(ValueError, "IHDR CRC"):
                inspect_candidate_archive(archive_path)

    def test_result_manifest_accepts_matching_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            payload = b"report fixture"
            (folder / "report.json").write_bytes(payload)
            manifest = {
                "run_id": "fixture-1",
                "source_sha256": "source-hash",
                "checkpoint_sha256": "checkpoint-hash",
                "artifacts": {
                    "report.json": {
                        "size": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                    }
                },
            }
            (folder / "artifact_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = verify_result_folder(folder)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["artifacts_verified"], ["report.json"])

    def test_result_manifest_rejects_modified_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            payload = b"expected"
            (folder / "report.json").write_bytes(b"modified")
            manifest = {
                "artifacts": {
                    "report.json": {
                        "size": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                    }
                }
            }
            (folder / "artifact_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "size mismatch|SHA-256 mismatch"):
                verify_result_folder(folder)

    def test_result_manifest_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            manifest = {"artifacts": {"../secret": {"size": 0, "sha256": ""}}}
            (folder / "artifact_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unsafe artifact path"):
                verify_result_folder(folder)


if __name__ == "__main__":
    unittest.main()
