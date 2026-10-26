"""Version 1.0.0 tests for OCTOMINER2 allowlisted workload controls (2026-10-26)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


CONTROL_ROOT = Path(__file__).resolve().parents[1] / "deployment" / "octo2-control"
sys.path.insert(0, str(CONTROL_ROOT))

import managed_services  # noqa: E402


class ManagedWorkloadTests(unittest.TestCase):
    def test_status_reports_running_health_and_boot_enabled(self) -> None:
        runner = Mock(
            return_value=SimpleNamespace(
                returncode=0,
                stdout=(
                    "LoadState=loaded\nActiveState=active\nSubState=running\n"
                    "MainPID=1234\nUnitFileState=enabled\n"
                ),
                stderr="",
            )
        )

        status = managed_services.workload_status(
            "qwen30b-vision", runner=runner, health_check=lambda port: port == 8080
        )

        self.assertEqual(status["name"], "Qwen 30B Vision")
        self.assertEqual(status["unit"], "qwen30b-vision.service")
        self.assertEqual(status["main_pid"], 1234)
        self.assertTrue(status["running"])
        self.assertTrue(status["api_ready"])
        self.assertTrue(status["enabled_at_boot"])

    def test_stop_uses_only_systemctl_stop_and_keeps_boot_state(self) -> None:
        runner = Mock(
            side_effect=[
                SimpleNamespace(returncode=0, stdout="", stderr=""),
                SimpleNamespace(
                    returncode=0,
                    stdout=(
                        "LoadState=loaded\nActiveState=inactive\nSubState=dead\n"
                        "MainPID=0\nUnitFileState=enabled\n"
                    ),
                    stderr="",
                ),
            ]
        )

        status = managed_services.transition_workload(
            "qwen30b-vision", "stop", runner=runner, health_check=lambda _port: False
        )

        self.assertEqual(runner.call_args_list[0].args[0], ["systemctl", "stop", "qwen30b-vision.service"])
        self.assertTrue(status["enabled_at_boot"])
        self.assertFalse(status["running"])
        self.assertFalse(status["api_ready"])

    def test_start_uses_only_systemctl_start(self) -> None:
        runner = Mock(
            side_effect=[
                SimpleNamespace(returncode=0, stdout="", stderr=""),
                SimpleNamespace(
                    returncode=0,
                    stdout=(
                        "LoadState=loaded\nActiveState=active\nSubState=running\n"
                        "MainPID=1234\nUnitFileState=enabled\n"
                    ),
                    stderr="",
                ),
            ]
        )

        status = managed_services.transition_workload(
            "qwen30b-vision", "start", runner=runner, health_check=lambda _port: True
        )

        self.assertEqual(runner.call_args_list[0].args[0], ["systemctl", "start", "qwen30b-vision.service"])
        self.assertTrue(status["running"])
        self.assertTrue(status["api_ready"])
        self.assertTrue(status["enabled_at_boot"])

    def test_unknown_workloads_and_actions_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown managed workload"):
            managed_services.workload_status("arbitrary-unit")
        with self.assertRaisesRegex(ValueError, "unknown managed workload"):
            managed_services.transition_workload("arbitrary-unit", "start")
        with self.assertRaisesRegex(ValueError, "action must be start or stop"):
            managed_services.transition_workload("qwen30b-vision", "enable")


if __name__ == "__main__":
    unittest.main()
