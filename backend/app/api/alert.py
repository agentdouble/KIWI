from fastapi import APIRouter, Depends
from app.services.alert_service import get_alert as read_alert, update_alert as write_alert
from app.schemas.alert import AlertResponse, AlertUpdateRequest
from app.models.user import User
from app.utils.auth import get_current_admin_user
from datetime import datetime

router = APIRouter(tags=["alert"])


@router.get("/alert", response_model=AlertResponse)
async def get_alert() -> AlertResponse:
    data = read_alert()
    # Parse updated_at to datetime if present
    updated_at = None
    if data.get("updated_at"):
        try:
            updated_at = datetime.fromisoformat(data["updated_at"])  # type: ignore[arg-type]
        except Exception:
            updated_at = None
    return AlertResponse(message=data.get("message", ""), active=bool(data.get("active", False)), updated_at=updated_at)


@router.put("/admin/alert", response_model=AlertResponse)
async def update_alert(payload: AlertUpdateRequest, current_admin: User = Depends(get_current_admin_user)) -> AlertResponse:  # noqa: ARG001
    data = write_alert(payload.message, payload.active)
    updated_at = None
    if data.get("updated_at"):
        try:
            updated_at = datetime.fromisoformat(data["updated_at"])  # type: ignore[arg-type]
        except Exception:
            updated_at = None
    return AlertResponse(message=data.get("message", ""), active=bool(data.get("active", False)), updated_at=updated_at)

