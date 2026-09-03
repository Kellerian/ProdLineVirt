"""Unit tests for Line Emulator layout config migration and ConfigFile fields."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from core.main_ui.config_migration import (
    enrich_legacy_config,
    migrate_legacy_config,
    needs_legacy_migration,
)
from core.main_ui.data import ConfigFile


LEGACY_PAYLOAD = {
    "printers": [{"name": "PRN_1", "port": 9100, "buffer": 2}],
    "cameras": [
        {
            "name": "CAM_1",
            "port": 10001,
            "config": {"packet_size": 1, "interval": 250},
        }
    ],
    "scanners": [
        {
            "name": "SCAN_1",
            "port_name": "COM3",
            "config": {
                "baud_rate": 9600,
                "bytesize": 8,
                "parity": "N",
                "stopbits": 1,
                "suffix": "\r\n",
            },
        }
    ],
    "transporters": [
        {"take_from": "SCAN_1", "give_to": "CAM_1", "interval": 100}
    ],
    "generators": [
        {
            "generator_type": "KM_01_14_21_13_93_4",
            "gtin": "07665585002196",
            "give_to": "CAM_1",
            "interval": 500,
        }
    ],
}

DEVICE_ID_SEQUENCE = [
    "id-transporter-1",
    "id-generator-1",
    "id-printer-1",
    "id-camera-1",
    "id-scanner-1",
]


class TestNeedsLegacyMigration(unittest.TestCase):
    """Tests for ``needs_legacy_migration`` detection helper."""

    def test_detects_missing_layout_fields(self) -> None:
        """Payload without order arrays requires migration."""
        self.assertTrue(needs_legacy_migration(LEGACY_PAYLOAD))

    def test_detects_missing_device_id(self) -> None:
        """Payload with layout fields but no device_id still requires migration."""
        payload = {
            "printers": [{"name": "PRN_1", "port": 9100}],
            "sidebar_order": [],
            "canvas_order": [],
        }
        self.assertTrue(needs_legacy_migration(payload))

    def test_modern_payload_does_not_need_migration(self) -> None:
        """Fully migrated payload is skipped by the validator hook."""
        payload = {
            "printers": [
                {
                    "device_id": "printer-fixed",
                    "name": "PRN_1",
                    "port": 9100,
                }
            ],
            "sidebar_order": [],
            "canvas_order": ["printer-fixed"],
            "dock_state": None,
        }
        self.assertFalse(needs_legacy_migration(payload))

    def test_non_mapping_input_does_not_need_migration(self) -> None:
        """Non-dict payloads are treated as already validated."""
        self.assertFalse(needs_legacy_migration([]))
        self.assertFalse(needs_legacy_migration(None))


class TestEnrichLegacyConfig(unittest.TestCase):
    """Direct tests for ``enrich_legacy_config`` without Pydantic validation."""

    @patch(
        "core.main_ui.config_migration.generate_device_id",
        side_effect=DEVICE_ID_SEQUENCE,
    )
    def test_sets_dock_state_default_and_order_arrays(self, _mock_ids: object) -> None:
        """Enrichment adds dock_state default and zone order arrays."""
        enriched = enrich_legacy_config(json.loads(json.dumps(LEGACY_PAYLOAD)))

        self.assertIsNone(enriched["dock_state"])
        self.assertEqual(
            enriched["sidebar_order"],
            ["id-transporter-1", "id-generator-1"],
        )
        self.assertEqual(
            enriched["canvas_order"],
            ["id-printer-1", "id-camera-1", "id-scanner-1"],
        )
        for key in ("printers", "cameras", "scanners", "transporters", "generators"):
            for item in enriched[key]:
                self.assertIn("device_id", item)
                self.assertFalse(item["advanced_expanded"])


class TestMigrateLegacyConfig(unittest.TestCase):
    """Tests for ``migrate_legacy_config`` helper."""

    @patch(
        "core.main_ui.config_migration.generate_device_id",
        side_effect=DEVICE_ID_SEQUENCE,
    )
    def test_assigns_device_id_and_advanced_defaults(self, _mock_ids: object) -> None:
        """Legacy devices receive generated ids and collapsed advanced sections."""
        config = migrate_legacy_config(LEGACY_PAYLOAD)

        self.assertEqual(config.printers[0].device_id, "id-printer-1")
        self.assertFalse(config.printers[0].advanced_expanded)
        self.assertEqual(config.cameras[0].device_id, "id-camera-1")
        self.assertFalse(config.scanners[0].advanced_expanded)
        self.assertEqual(config.transporters[0].device_id, "id-transporter-1")
        self.assertEqual(config.generators[0].device_id, "id-generator-1")

    @patch(
        "core.main_ui.config_migration.generate_device_id",
        side_effect=DEVICE_ID_SEQUENCE,
    )
    def test_builds_sidebar_and_canvas_order(self, _mock_ids: object) -> None:
        """Order arrays follow legacy list ordering by device zone."""
        config = migrate_legacy_config(LEGACY_PAYLOAD)

        self.assertEqual(
            config.sidebar_order,
            ["id-transporter-1", "id-generator-1"],
        )
        self.assertEqual(
            config.canvas_order,
            ["id-printer-1", "id-camera-1", "id-scanner-1"],
        )
        self.assertIsNone(config.dock_state)

    @patch(
        "core.main_ui.config_migration.generate_device_id",
        side_effect=DEVICE_ID_SEQUENCE,
    )
    def test_does_not_mutate_source_payload(self, _mock_ids: object) -> None:
        """Migration works on a copy and leaves the input mapping unchanged."""
        source = json.loads(json.dumps(LEGACY_PAYLOAD))
        migrate_legacy_config(source)

        self.assertNotIn("device_id", source["printers"][0])
        self.assertNotIn("sidebar_order", source)

    @patch(
        "core.main_ui.config_migration.generate_device_id",
        side_effect=["id-printer-1"],
    )
    def test_partial_migration_rebuilds_stale_canvas_order(
        self, _mock_ids: object
    ) -> None:
        """Stale canvas ids are replaced when legacy devices receive new ids."""
        payload = {
            "printers": [{"name": "PRN_1", "port": 9100, "buffer": 2}],
            "sidebar_order": [],
            "canvas_order": ["stale-printer-id"],
        }
        config = migrate_legacy_config(payload)

        self.assertEqual(config.printers[0].device_id, "id-printer-1")
        self.assertEqual(config.canvas_order, ["id-printer-1"])

    @patch(
        "core.main_ui.config_migration.generate_device_id",
        side_effect=["id-transporter-1", "id-generator-1"],
    )
    def test_partial_migration_rebuilds_empty_sidebar_order(
        self, _mock_ids: object
    ) -> None:
        """Empty sidebar order is rebuilt from transporter and generator list order."""
        payload = {
            "transporters": [
                {"take_from": "SCAN_1", "give_to": "CAM_1", "interval": 100}
            ],
            "generators": [
                {
                    "generator_type": "KM_01_14_21_13_93_4",
                    "gtin": "07665585002196",
                    "give_to": "CAM_1",
                    "interval": 500,
                }
            ],
            "sidebar_order": [],
            "canvas_order": [],
        }
        config = migrate_legacy_config(payload)

        self.assertEqual(
            config.sidebar_order,
            ["id-transporter-1", "id-generator-1"],
        )

    @patch(
        "core.main_ui.config_migration.generate_device_id",
        side_effect=["id-printer-1"],
    )
    def test_partial_migration_preserves_valid_canvas_order(
        self, _mock_ids: object
    ) -> None:
        """Existing canvas order is kept when every id is already known."""
        payload = {
            "printers": [
                {
                    "device_id": "printer-fixed",
                    "name": "PRN_1",
                    "port": 9100,
                }
            ],
            "sidebar_order": [],
            "canvas_order": ["printer-fixed"],
        }
        config = migrate_legacy_config(payload)

        self.assertEqual(config.printers[0].device_id, "printer-fixed")
        self.assertEqual(config.canvas_order, ["printer-fixed"])


class TestConfigFileLayoutFields(unittest.TestCase):
    """Tests for ConfigFile validation of legacy and modern JSON."""

    @patch(
        "core.main_ui.config_migration.generate_device_id",
        side_effect=DEVICE_ID_SEQUENCE,
    )
    def test_model_validate_json_accepts_legacy_payload(self, _mock_ids: object) -> None:
        """Legacy JSON without layout fields loads through automatic migration."""
        config = ConfigFile.model_validate_json(json.dumps(LEGACY_PAYLOAD))

        self.assertEqual(len(config.printers), 1)
        self.assertEqual(config.sidebar_order[0], "id-transporter-1")
        self.assertEqual(config.canvas_order[-1], "id-scanner-1")
        self.assertIsNone(config.dock_state)

    def test_model_validate_json_accepts_new_payload(self) -> None:
        """Modern JSON with explicit layout fields validates without migration."""
        payload = {
            "printers": [
                {
                    "device_id": "printer-fixed",
                    "name": "PRN_1",
                    "port": 9100,
                    "advanced_expanded": True,
                }
            ],
            "sidebar_order": [],
            "canvas_order": ["printer-fixed"],
            "dock_state": "YmFzZTY0LXN0YXRl",
        }
        config = ConfigFile.model_validate_json(json.dumps(payload))

        self.assertEqual(config.printers[0].device_id, "printer-fixed")
        self.assertTrue(config.printers[0].advanced_expanded)
        self.assertEqual(config.canvas_order, ["printer-fixed"])
        self.assertEqual(config.dock_state, "YmFzZTY0LXN0YXRl")

    def test_strict_defaults_for_optional_new_fields(self) -> None:
        """Strict mode keeps defaults for omitted optional layout fields."""
        payload = {
            "printers": [
                {
                    "device_id": "printer-fixed",
                    "name": "PRN_1",
                    "port": 9100,
                }
            ],
            "sidebar_order": [],
            "canvas_order": ["printer-fixed"],
        }
        config = ConfigFile.model_validate(payload)

        self.assertFalse(config.printers[0].advanced_expanded)
        self.assertIsNone(config.dock_state)

    @patch(
        "core.main_ui.config_migration.generate_device_id",
        side_effect=[
            "transporter-example-id",
            "generator-example-id",
            "camera-example-id",
            "scanner-example-id",
        ],
    )
    def test_scanner_example_json_loads(self, _mock_ids: object) -> None:
        """Real legacy sample config from configs/ opens without validation errors."""
        sample_path = Path("configs/scanner_example.json")
        config = ConfigFile.model_validate_json(sample_path.read_text(encoding="utf-8"))

        self.assertEqual(len(config.scanners), 1)
        self.assertEqual(len(config.generators), 1)
        self.assertEqual(len(config.transporters), 1)
        self.assertEqual(config.sidebar_order, [
            "transporter-example-id",
            "generator-example-id",
        ])
        self.assertEqual(config.canvas_order, [
            "camera-example-id",
            "scanner-example-id",
        ])


if __name__ == "__main__":
    unittest.main(verbosity=2)
