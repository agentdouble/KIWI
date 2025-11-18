from datetime import datetime
from fastapi import APIRouter, Depends
from app.models.user import User
from app.utils.auth import get_current_admin_user
from app.schemas.feature_updates import (
    FeatureUpdatesResponse,
    FeatureUpdatesUpdateRequest,
)
from app.services.feature_updates_service import (
    get_feature_updates as read_feature_updates,
    update_feature_updates as write_feature_updates,
)

router = APIRouter(tags=["feature-updates"])


@router.get("/feature-updates", response_model=FeatureUpdatesResponse)
async def get_feature_updates() -> FeatureUpdatesResponse:
    data = read_feature_updates()
    updated_at = None
    if data.get("updated_at"):
        try:
            updated_at = datetime.fromisoformat(data["updated_at"])  # type: ignore[arg-type]
        except Exception:
            updated_at = None
    return FeatureUpdatesResponse(
        active=bool(data.get("active", True)),
        title=data.get("title", "Nouveautés"),
        sections=data.get("sections", []),
        updated_at=updated_at,
    )


@router.put("/admin/feature-updates", response_model=FeatureUpdatesResponse)
async def update_feature_updates(
    payload: FeatureUpdatesUpdateRequest, current_admin: User = Depends(get_current_admin_user)  # noqa: ARG001
) -> FeatureUpdatesResponse:
    data = write_feature_updates(payload.active, payload.title, [s.model_dump() for s in payload.sections])
    updated_at = None
    if data.get("updated_at"):
        try:
            updated_at = datetime.fromisoformat(data["updated_at"])  # type: ignore[arg-type]
        except Exception:
            updated_at = None
    return FeatureUpdatesResponse(
        active=bool(data.get("active", True)),
        title=data.get("title", "Nouveautés"),
        sections=data.get("sections", []),
        updated_at=updated_at,
    )

