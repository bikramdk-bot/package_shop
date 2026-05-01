from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from urllib import error, request

APP_ROOT = Path(__file__).resolve().parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from paths import resolve_data
from shared.schemas import DeviceHeartbeat, DeviceRegistrationRequest


CONTROL_PLANE_STATE_PATH = resolve_data("cloud_device.json")
CONTROL_PLANE_URL = (os.environ.get("PACKAGE_SHOP_CONTROL_PLANE_URL") or "").strip().rstrip("/")
CONTROL_PLANE_ENABLED = (os.environ.get("PACKAGE_SHOP_CONTROL_PLANE_ENABLED") or "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
CONTROL_PLANE_ENVIRONMENT = (os.environ.get("PACKAGE_SHOP_ENVIRONMENT") or "production").strip() or "production"


def is_control_plane_enabled() -> bool:
    return CONTROL_PLANE_ENABLED and bool(CONTROL_PLANE_URL)


def get_control_plane_url() -> str:
    return CONTROL_PLANE_URL


def load_registration_state() -> Dict[str, Any]:
    path = Path(CONTROL_PLANE_STATE_PATH)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_registration_state(state: Dict[str, Any]) -> None:
    path = Path(CONTROL_PLANE_STATE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def get_registered_device_id() -> Optional[str]:
    registration = load_registration_state().get("registration") or {}
    device_id = registration.get("device_id")
    if not device_id:
        return None
    return str(device_id).strip() or None


def get_control_plane_status() -> Dict[str, Any]:
    state = load_registration_state()
    registration = state.get("registration") or {}
    return {
        "enabled": is_control_plane_enabled(),
        "url": get_control_plane_url(),
        "registered": bool(str(registration.get("device_id") or "").strip()),
        "device_id": str(registration.get("device_id") or "").strip(),
        "registered_at": str(registration.get("registered_at") or "").strip(),
        "lease_expires_at": str(registration.get("lease_expires_at") or "").strip(),
    }


def build_device_heartbeat(
    *,
    shop_id: str,
    device_serial: Optional[str],
    software_version: str,
    status: str,
    uptime_seconds: int,
    timestamp: str,
    scanner_configured: bool,
    printer_device: Optional[str],
    alerts: Optional[list[str]] = None,
) -> DeviceHeartbeat:
    alert_items = list(alerts or [])
    device_id = get_registered_device_id()
    fallback_device_id = (device_serial or "").strip() or "unregistered-device"
    if not device_id:
        device_id = fallback_device_id
        if is_control_plane_enabled():
            alert_items.append("device_not_registered")
    if not shop_id:
        alert_items.append("missing_shop_id")
    if not (device_serial or "").strip():
        alert_items.append("missing_device_serial")
    return DeviceHeartbeat(
        device_id=device_id,
        shop_id=shop_id or "UNKNOWN",
        software_version=software_version,
        status=status,
        uptime_seconds=max(0, int(uptime_seconds)),
        timestamp=timestamp,
        scanner_configured=scanner_configured,
        printer_device=printer_device,
        alerts=[item for item in alert_items if item],
    )


def register_device(
    *,
    shop_id: str,
    device_serial: str,
    software_version: str,
    device_name: Optional[str] = None,
    timeout: int = 5,
) -> Dict[str, Any]:
    if not is_control_plane_enabled():
        raise RuntimeError("control plane is disabled")

    payload = DeviceRegistrationRequest(
        shop_id=shop_id,
        device_serial=device_serial,
        software_version=software_version,
        device_name=device_name,
        environment=CONTROL_PLANE_ENVIRONMENT,
    ).to_dict()
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{CONTROL_PLANE_URL}/device/register",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"registration failed: {exc.code} {detail}".strip()) from exc
    except error.URLError as exc:
        raise RuntimeError(f"registration failed: {exc.reason}") from exc

    try:
        response_payload = json.loads(raw)
    except Exception as exc:
        raise RuntimeError("registration failed: invalid JSON response") from exc

    registration = response_payload.get("registration")
    if not isinstance(registration, dict) or not str(registration.get("device_id") or "").strip():
        raise RuntimeError("registration failed: missing registration payload")

    state = {
        "request": payload,
        "registration": registration,
        "control_plane_url": CONTROL_PLANE_URL,
    }
    save_registration_state(state)
    return state