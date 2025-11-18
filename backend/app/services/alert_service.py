import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

ALERT_STORAGE_PATH = Path(__file__).resolve().parent.parent.parent / "storage" / "alert.json"


def _ensure_storage_dir() -> None:
    ALERT_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_alert() -> Dict[str, Any]:
    """Read the system alert from storage. Returns defaults if missing."""
    try:
        if ALERT_STORAGE_PATH.exists():
            with open(ALERT_STORAGE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Backward/robust defaulting
                return {
                    "message": data.get("message", ""),
                    "active": bool(data.get("active", False)),
                    "updated_at": data.get("updated_at"),
                }
    except Exception:
        # On any read/parse error, return safe defaults
        pass

    return {"message": "", "active": False, "updated_at": None}


def update_alert(message: str, active: bool) -> Dict[str, Any]:
    """Persist the system alert to storage and return the new value."""
    _ensure_storage_dir()
    payload = {
        "message": message or "",
        "active": bool(active),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(ALERT_STORAGE_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload

