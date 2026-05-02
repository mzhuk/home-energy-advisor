from fastapi import APIRouter, Request, status

from app.core.settings import Settings
from app.homes.schemas import HomeCreateRequest, HomeDetail, HomeProfile
from app.homes.service import create_home, get_home, list_homes

router = APIRouter(prefix="/homes", tags=["homes"])


def _settings(request: Request) -> Settings:
    return request.app.state.settings


@router.get("", response_model=list[HomeProfile])
def list_home_profiles(request: Request) -> list[HomeProfile]:
    return list_homes(_settings(request).database_url)


@router.post("", response_model=HomeDetail, status_code=status.HTTP_201_CREATED)
def create_home_profile(request: Request, payload: HomeCreateRequest) -> HomeDetail:
    return create_home(_settings(request).database_url, payload)


@router.get("/{home_id}", response_model=HomeDetail)
def get_home_profile(request: Request, home_id: str) -> HomeDetail:
    return get_home(_settings(request).database_url, home_id)
