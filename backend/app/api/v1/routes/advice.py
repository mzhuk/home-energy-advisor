from fastapi import APIRouter, Request, status

from app.advice.models import AdviceRecord
from app.advice.service import generate_advice, get_latest_advice
from app.core.settings import Settings

router = APIRouter(prefix="/homes/{home_id}/advice", tags=["advice"])


def _settings(request: Request) -> Settings:
    return request.app.state.settings


@router.get("", response_model=AdviceRecord)
def get_home_advice(request: Request, home_id: str) -> AdviceRecord:
    return get_latest_advice(_settings(request).database_url, home_id)


@router.post("", response_model=AdviceRecord, status_code=status.HTTP_201_CREATED)
def generate_home_advice(request: Request, home_id: str) -> AdviceRecord:
    return generate_advice(_settings(request), home_id)

