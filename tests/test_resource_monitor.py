from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import tempfile
import unittest
import os
import json
from pathlib import Path
from unittest.mock import patch

import yomu.runtime.resource_monitor as resource_monitor
from yomu.config import settings
from yomu.runtime.resource_monitor import ResourceMonitor


class ResourceMonitorTests(unittest.TestCase):
    def test_resource_monitoring_defaults_to_enabled(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(settings._env_bool("RESOURCE_MONITORING", True))

    def test_disabled_monitor_is_safe_without_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            monitor = ResourceMonitor(tmp, enabled=False)
            self.assertEqual(monitor.interval_seconds, 5.0)
            monitor.start()
            summary = monitor.stop()
            self.assertFalse(summary["enabled"])
            self.assertIn("reason", summary)

    def test_missing_psutil_disables_monitor(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(resource_monitor, "psutil", None):
                monitor = ResourceMonitor(tmp, enabled=True)
                self.assertFalse(monitor.enabled)
                summary = monitor.stop()
                self.assertFalse(summary["enabled"])

    def test_report_writer_uses_existing_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            monitor = ResourceMonitor(tmp, enabled=False)
            monitor.enabled = True
            monitor.samples = [
                {
                    "timestamp": 1.0,
                    "elapsed_s": 0.0,
                    "stage": "ocr",
                    "pages_done": 1,
                    "pages_total": 2,
                    "queue_depth": 1,
                    "active_workers": 1,
                    "parent_pid": 100,
                    "parent_rss_mb": 500.0,
                    "parent_vms_mb": 900.0,
                    "parent_cpu_percent": 20.0,
                    "parent_threads": 4,
                    "child_count": 1,
                    "children_rss_mb": 1500.0,
                    "total_pipeline_rss_mb": 2000.0,
                    "system_used_mb": 8000.0,
                    "system_available_mb": 12000.0,
                    "system_ram_percent": 50.0,
                    "swap_used_mb": 0.0,
                    "cpu_percent": 80.0,
                    "children": [
                        {
                            "pid": 200,
                            "role": "ocr-worker",
                            "rss_mb": 1500.0,
                            "cpu_percent": 90.0,
                        }
                    ],
                }
            ]
            summary = monitor.write_reports()
            self.assertTrue(summary["enabled"])
            self.assertEqual(summary["sample_count"], 1)
            self.assertEqual(summary["total_pipeline_rss_mb_peak"], 2000.0)
            self.assertEqual(summary["system_used_mb_peak"], 8000.0)
            self.assertEqual(summary["swap_used_mb_peak"], 0.0)
            self.assertEqual(summary["ocr_worker_rss_mb_peak"], 1500.0)
            self.assertTrue(Path(summary["resource_report_json"]).is_file())
            self.assertEqual(summary["resource_report_html"], "")
            self.assertFalse((Path(tmp) / "resource_report.html").exists())
            self.assertTrue(Path(summary["resource_timeline_csv"]).is_file())

    def test_sample_time_is_reported_for_timing_attribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            monitor = ResourceMonitor(tmp, enabled=True, interval_seconds=5.0)
            monitor.start()
            monitor._sample_once()
            summary = monitor.stop()
            self.assertEqual(summary["sample_count"], 2)
            self.assertGreater(summary["sampling_seconds"], 0.0)
            report = json.loads(Path(summary["resource_report_json"]).read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["sample_count"], 2)
            self.assertGreater(report["summary"]["sampling_seconds"], 0.0)

    def test_html_report_is_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            monitor = ResourceMonitor(tmp, enabled=False, generate_html=True)
            monitor.enabled = True
            summary = monitor.write_reports()
            self.assertTrue(Path(summary["resource_report_html"]).is_file())


if __name__ == "__main__":
    unittest.main()
