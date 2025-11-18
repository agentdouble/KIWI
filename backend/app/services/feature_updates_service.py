import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

FEATURE_UPDATES_PATH = Path(__file__).resolve().parent.parent.parent / "storage" / "feature_updates.json"


def _ensure_storage_dir() -> None:
    FEATURE_UPDATES_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_feature_updates() -> Dict[str, Any]:
    """Read feature updates config from storage, with sensible defaults."""
    try:
        if FEATURE_UPDATES_PATH.exists():
            with open(FEATURE_UPDATES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "active": bool(data.get("active", True)),
                    "title": data.get("title", "Nouveautés"),
                    "sections": data.get("sections", []),
                    "updated_at": data.get("updated_at"),
                }
    except Exception:
        pass

    # Default content similar to current hardcoded popup
    return {
        "active": True,
        "title": "Nouveautés dans FoyerGPT",
        "sections": [
            {
                "title": "Nouvelle fonctionnalité",
                "items": [
                    "Agent de création de PowerPoint : générez vos PowerPoint directement depuis FoyerGPT",
                    "Modification instantanée du dernier message : éditez la bulle, annulez ou renvoyez en un clic",
                    "Glisser-déposer de documents sur toute la page (PDF, Word, Markdown, images, etc.)",
                ],
            },
            {
                "title": "Améliorations majeures",
                "items": [
                    "Discussion avec document contenant des images",
                    "Les images (PNG, JPG, GIF, WebP) sont désormais analysées comme les PDF et DOCX",
                ],
            },
            {
                "title": "Fonctionnalités mineures",
                "items": [
                    "Feedback",
                    "Mise en favoris des GPTs préférés",
                    "Dashboard admin",
                    "Classement des agents les plus utilisés",
                ],
            },
        ],
        "updated_at": None,
    }


def update_feature_updates(active: bool, title: str, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    _ensure_storage_dir()
    payload = {
        "active": bool(active),
        "title": title or "Nouveautés",
        "sections": sections or [],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(FEATURE_UPDATES_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload

