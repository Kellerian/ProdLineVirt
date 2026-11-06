"""Unit tests for controller configuration models and ConfigFile.controllers."""

from __future__ import annotations

import json
import unittest

from pydantic import ValidationError

from core.controller.data import ControllerConfig, ControllerMode, ControllerType
from core.main_ui.data import ConfigFile


class TestControllerConfig(unittest.TestCase):
    """Tests for ControllerConfig JSON and defaults."""

    def test_defaults_queue_mode_type(self) -> None:
        """Missing queue_size, mode, controller_type use documented defaults."""
        config = ControllerConfig.model_validate({"name": "CTL_1", "port": 5020})
        self.assertEqual(config.queue_size, 10)
        self.assertEqual(config.mode, ControllerMode.simplex)
        self.assertEqual(config.controller_type, ControllerType.delta)
        self.assertEqual(config.register_addresses, [])

    def test_register_addresses_missing_in_json_defaults_to_empty_list(self) -> None:
        """Omitted register_addresses in JSON yields []."""
        payload = json.dumps({"name": "CTL_1", "port": 5020})
        config = ControllerConfig.model_validate_json(payload)
        self.assertEqual(config.register_addresses, [])

    def test_register_addresses_round_trip_preserves_order(self) -> None:
        """JSON round-trip keeps register address order."""
        addresses = [4146, 5000, 4146]
        original = ControllerConfig(
            name="CTL_1",
            port=5020,
            register_addresses=addresses,
        )
        restored = ControllerConfig.model_validate_json(original.model_dump_json())
        self.assertEqual(restored.register_addresses, addresses)

    def test_register_addresses_boundary_ok(self) -> None:
        """0 and 10000 are valid register indices."""
        cfg = ControllerConfig.model_validate(
            {
                "name": "CTL_1",
                "port": 5020,
                "register_addresses": [0, 10000],
            },
        )
        self.assertEqual(cfg.register_addresses, [0, 10000])

    def test_register_address_out_of_range_raises(self) -> None:
        """Values below 0 or above 10000 raise ValidationError."""
        for bad in (-1, 10001):
            with self.subTest(address=bad):
                with self.assertRaises(ValidationError):
                    ControllerConfig.model_validate(
                        {
                            "name": "CTL_1",
                            "port": 5020,
                            "register_addresses": [4146, bad],
                        },
                    )

    def test_register_addresses_bool_element_raises(self) -> None:
        """Strict config: bool is not accepted as int in register_addresses."""
        for flag in (True, False):
            with self.subTest(register_addresses_element=flag):
                with self.assertRaises(ValidationError):
                    ControllerConfig.model_validate(
                        {
                            "name": "CTL_1",
                            "port": 5020,
                            "register_addresses": [flag],
                        },
                    )

    def test_register_addresses_string_element_raises(self) -> None:
        """String digits are not coerced to int in register_addresses."""
        with self.assertRaises(ValidationError):
            ControllerConfig.model_validate(
                {
                    "name": "CTL_1",
                    "port": 5020,
                    "register_addresses": ["4146"],
                },
            )

    def test_register_addresses_float_element_raises(self) -> None:
        """Non-int elements (e.g. float) raise ValidationError under strict."""
        with self.assertRaises(ValidationError):
            ControllerConfig.model_validate(
                {
                    "name": "CTL_1",
                    "port": 5020,
                    "register_addresses": [4146.0],
                },
            )

    def test_register_addresses_null_raises(self) -> None:
        """Explicit null for register_addresses is invalid (no coercion to [])."""
        with self.assertRaises(ValidationError):
            ControllerConfig.model_validate_json(
                '{"name": "CTL_1", "port": 5020, "register_addresses": null}',
            )

    def test_all_mode_type_combinations_round_trip(self) -> None:
        """Each mode/type pair survives model_dump_json → model_validate_json."""
        for mode in ControllerMode:
            for controller_type in ControllerType:
                original = ControllerConfig(
                    name="CTL_1",
                    port=5020,
                    queue_size=5,
                    mode=mode,
                    controller_type=controller_type,
                )
                restored = ControllerConfig.model_validate_json(original.model_dump_json())
                self.assertEqual(restored.mode, mode)
                self.assertEqual(restored.controller_type, controller_type)

    def test_controller_config_string_fields_round_trip(self) -> None:
        """mode and controller_type accept JSON strings under strict Config."""
        payload = json.dumps(
            {
                "name": "CTL_1",
                "port": 5020,
                "queue_size": 7,
                "mode": "duplex",
                "controller_type": "xinje",
            },
        )
        config = ControllerConfig.model_validate_json(payload)
        self.assertEqual(config.mode, ControllerMode.duplex)
        self.assertEqual(config.controller_type, ControllerType.xinje)

    def test_invalid_mode_string_raises(self) -> None:
        """Unknown mode string raises ValidationError."""
        with self.assertRaises(ValidationError):
            ControllerConfig.model_validate(
                {
                    "name": "CTL_1",
                    "port": 5020,
                    "mode": "triplex",
                },
            )

    def test_invalid_controller_type_string_raises(self) -> None:
        """Unknown controller_type string raises ValidationError."""
        with self.assertRaises(ValidationError):
            ControllerConfig.model_validate(
                {
                    "name": "CTL_1",
                    "port": 5020,
                    "controller_type": "siemens",
                },
            )

    def test_queue_size_negative_raises(self) -> None:
        """queue_size below 1 raises ValidationError."""
        with self.assertRaises(ValidationError):
            ControllerConfig.model_validate(
                {
                    "name": "CTL_1",
                    "port": 5020,
                    "queue_size": -1,
                },
            )

    def test_queue_size_zero_raises(self) -> None:
        """queue_size 0 raises ValidationError."""
        with self.assertRaises(ValidationError):
            ControllerConfig.model_validate(
                {
                    "name": "CTL_1",
                    "port": 5020,
                    "queue_size": 0,
                },
            )

    def test_queue_size_above_1000_raises(self) -> None:
        """queue_size above 1000 raises ValidationError."""
        with self.assertRaises(ValidationError):
            ControllerConfig.model_validate(
                {
                    "name": "CTL_1",
                    "port": 5020,
                    "queue_size": 1001,
                },
            )

    def test_non_string_mode_raises(self) -> None:
        """Non-string mode in JSON raises ValidationError."""
        with self.assertRaises(ValidationError):
            ControllerConfig.model_validate(
                {
                    "name": "CTL_1",
                    "port": 5020,
                    "mode": 1,
                },
            )

    def test_non_string_controller_type_raises(self) -> None:
        """Non-string controller_type in JSON raises ValidationError."""
        with self.assertRaises(ValidationError):
            ControllerConfig.model_validate(
                {
                    "name": "CTL_1",
                    "port": 5020,
                    "controller_type": ["delta"],
                },
            )


class TestConfigFileControllers(unittest.TestCase):
    """Tests for ConfigFile controllers section and backward compatibility."""

    def test_legacy_json_only_printers_has_empty_controllers(self) -> None:
        """Old JSON with printers only validates; controllers defaults to []."""
        legacy = json.dumps({"printers": [{"name": "PRN_1", "port": 9100}]})
        config = ConfigFile.model_validate_json(legacy)
        self.assertEqual(config.controllers, [])
        self.assertEqual(len(config.printers), 1)

    def test_controllers_round_trip_in_config_file(self) -> None:
        """controllers section survives model_dump_json → model_validate_json."""
        original = ConfigFile(
            controllers=[
                ControllerConfig(
                    name="CTL_5020",
                    port=5020,
                    queue_size=10,
                    mode=ControllerMode.simplex,
                    controller_type=ControllerType.delta,
                ),
                ControllerConfig(
                    name="CTL_5021",
                    port=5021,
                    queue_size=12,
                    mode=ControllerMode.duplex,
                    controller_type=ControllerType.xinje,
                ),
            ],
        )
        restored = ConfigFile.model_validate_json(original.model_dump_json())
        self.assertEqual(len(restored.controllers), 2)
        self.assertEqual(restored.controllers[0].name, "CTL_5020")
        self.assertEqual(restored.controllers[1].mode, ControllerMode.duplex)
        self.assertEqual(restored.controllers[1].controller_type, ControllerType.xinje)


if __name__ == "__main__":
    unittest.main(verbosity=2)
