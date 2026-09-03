"""Migration helpers for legacy Line Emulator project JSON."""

from __future__ import annotations

import copy
from typing import Any

import shortuuid

from core.main_ui.data import ConfigFile

DEVICE_LIST_KEYS: tuple[str, ...] = (
    "printers",
    "cameras",
    "scanners",
    "transporters",
    "generators",
)
SIDEBAR_DEVICE_KEYS: tuple[str, ...] = ("transporters", "generators")
CANVAS_DEVICE_KEYS: tuple[str, ...] = ("printers", "cameras", "scanners")


def generate_device_id() -> str:
    """Generate a stable short identifier for a device configuration entry.

    Returns:
        Random device identifier suitable for layout persistence.
    """
    return shortuuid.uuid()


def needs_legacy_migration(data: Any) -> bool:
    """Return whether ``data`` lacks layout fields or per-device identifiers.

    Args:
        data: Raw configuration mapping, typically parsed project JSON.

    Returns:
        ``True`` when migration should enrich the payload before validation.
    """
    if not isinstance(data, dict):
        return False
    if "sidebar_order" not in data or "canvas_order" not in data:
        return True
    for key in DEVICE_LIST_KEYS:
        for item in data.get(key, []):
            if isinstance(item, dict) and "device_id" not in item:
                return True
    return False


def _ensure_device_fields(items: list[Any]) -> tuple[list[str], bool]:
    """Assign ``device_id`` and ``advanced_expanded`` defaults to device dicts.

    Args:
        items: Device configuration dictionaries from a project file section.

    Returns:
        Tuple of ordered ``device_id`` values and whether any new id was generated.
    """
    device_ids: list[str] = []
    any_generated = False
    for item in items:
        if not isinstance(item, dict):
            continue
        if "device_id" not in item:
            item["device_id"] = generate_device_id()
            any_generated = True
        item.setdefault("advanced_expanded", False)
        device_ids.append(item["device_id"])
    return device_ids, any_generated


def _collect_zone_device_ids(
    data: dict[str, Any],
    keys: tuple[str, ...],
) -> tuple[list[str], bool]:
    """Ensure device fields and collect ordered ids for a layout zone.

    Args:
        data: Configuration mapping being migrated.
        keys: Device list keys belonging to the layout zone.

    Returns:
        Tuple of ordered device ids and whether any new id was generated.
    """
    ordered_ids: list[str] = []
    any_generated = False
    for key in keys:
        ids, generated = _ensure_device_fields(data.setdefault(key, []))
        ordered_ids.extend(ids)
        any_generated = any_generated or generated
    return ordered_ids, any_generated


def _order_needs_rebuild(order: Any, valid_ids: set[str]) -> bool:
    """Return whether a persisted order list is empty or references unknown ids.

    Args:
        order: Existing ``sidebar_order`` or ``canvas_order`` value.
        valid_ids: Device ids present in the corresponding layout zone.

    Returns:
        ``True`` when the order should be rebuilt from device list order.
    """
    if not isinstance(order, list) or not order:
        return True
    return any(
        not isinstance(device_id, str) or device_id not in valid_ids
        for device_id in order
    )


def enrich_legacy_config(data: dict[str, Any]) -> dict[str, Any]:
    """Enrich legacy project JSON with layout and per-device persistence fields.

    Sidebar order follows ``transporters`` then ``generators`` list order.
    Canvas order follows ``printers``, ``cameras``, then ``scanners`` list order.
    When layout arrays already exist but devices still lack ``device_id``, or the
    persisted order is empty or references unknown ids, order arrays are rebuilt
    from list order after identifiers are assigned.

    Args:
        data: Legacy or partially migrated configuration mapping.

    Returns:
        Mapping ready for ``ConfigFile.model_validate``.
    """
    sidebar_device_ids, sidebar_ids_generated = _collect_zone_device_ids(
        data, SIDEBAR_DEVICE_KEYS
    )
    existing_sidebar_order = data.get("sidebar_order")
    if (
        "sidebar_order" not in data
        or sidebar_ids_generated
        or _order_needs_rebuild(existing_sidebar_order, set(sidebar_device_ids))
    ):
        data["sidebar_order"] = sidebar_device_ids

    canvas_device_ids, canvas_ids_generated = _collect_zone_device_ids(
        data, CANVAS_DEVICE_KEYS
    )
    existing_canvas_order = data.get("canvas_order")
    if (
        "canvas_order" not in data
        or canvas_ids_generated
        or _order_needs_rebuild(existing_canvas_order, set(canvas_device_ids))
    ):
        data["canvas_order"] = canvas_device_ids

    data.setdefault("dock_state", None)
    return data


def migrate_legacy_config(data: dict[str, Any]) -> ConfigFile:
    """Migrate legacy project JSON to a validated ``ConfigFile`` instance.

    Args:
        data: Legacy configuration without ``device_id`` and/or layout fields.

    Returns:
        Validated configuration with generated identifiers and default layout.
    """
    migrated = enrich_legacy_config(copy.deepcopy(data))
    return ConfigFile.model_validate(migrated)
