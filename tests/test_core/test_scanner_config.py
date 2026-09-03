"""Unit tests for scanner configuration models and ConfigFile scanners section."""

from __future__ import annotations

import json
import unittest

from core.barcode_scanner.data import ScannerConfig, ScannerParams
from core.main_ui.data import ConfigFile
from libs.serial_port import SerialPortConfig


class TestScannerParams(unittest.TestCase):
    """Tests for ScannerParams defaults and validation."""

    def test_defaults_match_serial_line_settings(self) -> None:
        """Default params match typical scanner serial settings."""
        params = ScannerParams()
        self.assertEqual(params.baud_rate, 9600)
        self.assertEqual(params.bytesize, 8)
        self.assertEqual(params.parity, "N")
        self.assertEqual(params.stopbits, 1)
        self.assertEqual(params.suffix, "\r\n")


class TestScannerConfig(unittest.TestCase):
    """Tests for ScannerConfig and to_serial_port_config."""

    def test_to_serial_port_config_maps_fields(self) -> None:
        """ScannerConfig builds SerialPortConfig with port and line params."""
        config = ScannerConfig(
            device_id="scan-test-id",
            name="SCAN_1",
            port_name="COM7",
            config=ScannerParams(
                baud_rate=115200,
                bytesize=7,
                parity="E",
                stopbits=2,
                suffix="\n",
            ),
        )
        serial_cfg = config.to_serial_port_config()
        self.assertIsInstance(serial_cfg, SerialPortConfig)
        self.assertEqual(serial_cfg.port_name, "COM7")
        self.assertEqual(serial_cfg.baud_rate, 115200)
        self.assertEqual(serial_cfg.bytesize, 7)
        self.assertEqual(serial_cfg.parity, "E")
        self.assertEqual(serial_cfg.stopbits, 2)
        self.assertEqual(serial_cfg.suffix, "\n")


class TestConfigFileScanners(unittest.TestCase):
    """Tests for ConfigFile scanners JSON round-trip and backward compatibility."""

    def test_empty_scanners_by_default(self) -> None:
        """ConfigFile without scanners key uses an empty list."""
        config = ConfigFile.model_validate({})
        self.assertEqual(config.scanners, [])

    def test_round_trip_json_with_scanners(self) -> None:
        """scanners section survives model_dump_json → model_validate_json."""
        original = ConfigFile(
            scanners=[
                ScannerConfig(
                    device_id="scan-roundtrip-id",
                    name="SCAN_1",
                    port_name="COM3",
                    config=ScannerParams(),
                )
            ]
        )
        restored = ConfigFile.model_validate_json(original.model_dump_json())
        self.assertEqual(len(restored.scanners), 1)
        self.assertEqual(restored.scanners[0].name, "SCAN_1")
        self.assertEqual(restored.scanners[0].port_name, "COM3")

    def test_legacy_json_without_scanners_is_compatible(self) -> None:
        """Legacy config JSON without scanners section loads successfully."""
        legacy = json.dumps(
            {
                "printers": [{"name": "PRN_1", "port": 9100}],
                "cameras": [
                    {
                        "name": "CAM_1",
                        "port": 10001,
                        "config": {"packet_size": 1, "interval": 250},
                    }
                ],
            }
        )
        config = ConfigFile.model_validate_json(legacy)
        self.assertEqual(config.scanners, [])
        self.assertEqual(len(config.printers), 1)
        self.assertEqual(len(config.cameras), 1)
        self.assertEqual(config.printers[0].device_id, config.canvas_order[0])

    def test_mixed_config_preserves_all_device_sections(self) -> None:
        """Full config keeps printers, cameras and scanners together."""
        payload = {
            "printers": [{"name": "PRN_1", "port": 9100}],
            "cameras": [
                {
                    "name": "CAM_1",
                    "port": 10001,
                    "config": {"packet_size": 1, "interval": 250},
                }
            ],
            "scanners": [
                {
                    "name": "SCAN_2",
                    "port_name": "COM5",
                    "config": {
                        "baud_rate": 9600,
                        "bytesize": 8,
                        "parity": "N",
                        "stopbits": 1,
                        "suffix": "\r\n",
                    },
                }
            ],
            "transporters": [],
            "generators": [],
        }
        config = ConfigFile.model_validate(payload)
        self.assertEqual(config.scanners[0].port_name, "COM5")
        self.assertEqual(config.printers[0].name, "PRN_1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
