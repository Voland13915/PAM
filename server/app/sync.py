from fastapi import APIRouter, Depends

from .auth import require_auth
from .errors import ApiError, json_response
from .scheduler import runner

router = APIRouter()


@router.get("/sync")
async def sync_status(user_id: int = Depends(require_auth)):
    return json_response(runner.status())


@router.post("/sync")
async def start_sync(user_id: int = Depends(require_auth)):
    if not runner.start("вручную"):
        raise ApiError(409, "SYNC_RUNNING", "Цены уже обновляются")
    return json_response(runner.status(), status=202)
