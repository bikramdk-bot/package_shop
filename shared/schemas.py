from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _require_str(payload: Dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if value is None:
        raise ValueError(f"missing required field: {key}")
    text = str(value).strip()
    if not text:
        raise ValueError(f"missing required field: {key}")
    return text


def _optional_str(payload: Dict[str, Any], key: str) -> Optional[str]:
    value = payload.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


@dataclass
class DeviceRegistrationRequest:
    shop_id: str
    device_serial: str
    software_version: str
    device_name: Optional[str] = None
    environment: str = "production"

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "DeviceRegistrationRequest":
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        return cls(
            shop_id=_require_str(payload, "shop_id"),
            device_serial=_require_str(payload, "device_serial"),
            software_version=_require_str(payload, "software_version"),
            device_name=_optional_str(payload, "device_name"),
            environment=_optional_str(payload, "environment") or "production",
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DeviceRegistrationResponse:
    device_id: str
    registered_at: str
    lease_expires_at: str
    status: str = "registered"

    @classmethod
    def issue(cls, lease_expires_at: Optional[str] = None) -> "DeviceRegistrationResponse":
        return cls(
            device_id=str(uuid4()),
            registered_at=_utc_now_iso(),
            lease_expires_at=lease_expires_at or _utc_now_iso(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DeviceHeartbeat:
    device_id: str
    shop_id: str
    software_version: str
    status: str
    uptime_seconds: int
    timestamp: str
    scanner_configured: bool = False
    printer_device: Optional[str] = None
    alerts: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "DeviceHeartbeat":
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        uptime_value = payload.get("uptime_seconds", 0)
        try:
            uptime_seconds = int(uptime_value)
        except Exception as exc:
            raise ValueError("uptime_seconds must be an integer") from exc
        alerts_value = payload.get("alerts") or []
        if not isinstance(alerts_value, list):
            raise ValueError("alerts must be a list")
        return cls(
            device_id=_require_str(payload, "device_id"),
            shop_id=_require_str(payload, "shop_id"),
            software_version=_require_str(payload, "software_version"),
            status=_optional_str(payload, "status") or "ok",
            uptime_seconds=max(0, uptime_seconds),
            timestamp=_optional_str(payload, "timestamp") or _utc_now_iso(),
            scanner_configured=bool(payload.get("scanner_configured")),
            printer_device=_optional_str(payload, "printer_device"),
            alerts=[str(item).strip() for item in alerts_value if str(item).strip()],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
