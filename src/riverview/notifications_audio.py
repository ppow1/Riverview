"""Bounded adapter from Riverview notifications to the existing Estate presenter."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

from riverview.database import connect
from riverview.notifications import NotificationStore


_ALLOWED_TYPES = {"blocked_requires_steward", "ready_for_steward_review"}


def check_annunciation_capability() -> dict[str, Any]:
    """Check the actual in-process WindowsPresenter dependencies."""
    if os.name != "nt":
        return {"available": False, "reason": "WindowsPresenter requires Windows", "estate_process_required": False}
    try:
        import winsound  # noqa: F401
    except Exception as exc:
        return {"available": False, "reason": f"winsound unavailable: {type(exc).__name__}", "estate_process_required": False}
    powershell = shutil.which("powershell") or shutil.which("powershell.exe")
    if not powershell:
        return {"available": False, "reason": "PowerShell unavailable", "estate_process_required": False}
    result = subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", "Add-Type -AssemblyName System.Speech"],
        check=False, capture_output=True, text=True, timeout=5,
    )
    if result.returncode:
        return {"available": False, "reason": "System.Speech unavailable", "estate_process_required": False}
    return {
        "available": True,
        "presenter": "estate.core.steward_annunciator.WindowsPresenter",
        "dependencies": ["winsound", "PowerShell", "System.Speech"],
        "estate_process_required": False,
        "output_endpoint": "current Windows interactive user's default audio endpoint",
    }


def _estate_presenter():
    # The Estate repository is a separate authoritative checkout. Prefer its
    # canonical Windows source root; retain the historical sibling fallback for
    # portable/test layouts. Do not silently substitute a second presenter.
    candidates = (
        Path(r"A:\theestate\src"),
        Path(__file__).resolve().parents[3] / "src",
    )
    estate_src = next((path for path in candidates if path.is_dir()), None)
    if estate_src is None:
        raise RuntimeError("RIV-NOT-0004: canonical Estate source root is unavailable.")
    if str(estate_src) not in sys.path:
        sys.path.insert(0, str(estate_src))
    from estate.core.steward_annunciator import WindowsPresenter

    return WindowsPresenter()


def deliver_steward_notification(
    notification_id: UUID,
    *,
    presenter: Any | None = None,
) -> dict[str, Any]:
    """Ding, speak, and mark one queued Steward notification delivered.

    The canonical notification row remains the source of truth. A delivery
    failure leaves it queued and is returned as a truthful result. This adapter
    does not acknowledge or accept the notification.
    """
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT notification_type,summary,state FROM steward_notifications WHERE notification_id=%s",
            (notification_id,),
        )
        row = cursor.fetchone()
    if row is None:
        return {"delivered": False, "reason": "notification_not_found", "notification_id": str(notification_id)}
    notification_type, summary, state = row
    if notification_type not in _ALLOWED_TYPES:
        return {"delivered": False, "reason": "notification_type_not_audio_deliverable", "state": state}
    if state != "queued":
        return {"delivered": False, "reason": "notification_not_queued", "state": state}
    capability = check_annunciation_capability()
    if not capability["available"]:
        return {"delivered": False, "reason": "audio_delivery_unavailable", "state": "queued", "capability": capability}

    adapter = presenter or _estate_presenter()
    try:
        if hasattr(adapter, "announce"):
            adapter.announce({"title": notification_type, "summary": summary})
        else:
            adapter.ding()
            adapter.speak(summary)
    except Exception as exc:
        return {
            "delivered": False,
            "reason": "audio_delivery_failed",
            "notification_id": str(notification_id),
            "error": f"{type(exc).__name__}: {exc}",
            "state": "queued",
        }

    NotificationStore().mark_delivered(notification_id)
    return {
        "delivered": True,
        "notification_id": str(notification_id),
        "notification_type": notification_type,
        "delivery_path": "estate.core.steward_annunciator.WindowsPresenter",
        "acknowledged": False,
    }
