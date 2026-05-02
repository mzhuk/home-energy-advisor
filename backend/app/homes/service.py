from typing import Any

from app.advice.repository import get_latest_advice
from app.core.errors import NotFoundError
from app.db.connection import connect
from app.db.ids import new_id
from app.homes.ai_context import build_ai_context
from app.homes.repository import create_home as create_home_record
from app.homes.repository import get_home as get_home_record
from app.homes.repository import list_homes as list_home_records
from app.homes.schemas import HomeCreateRequest, HomeDetail, HomeProfile


def _home_profile_from_record(record: dict[str, Any]) -> HomeProfile:
    return HomeProfile(
        id=str(record["id"]),
        name=str(record["name"]),
        build_period=record["build_period"],
        home_size=record["home_size"],
        residents=record["residents"],
        heating_system=record["heating_system"],
        has_ev=bool(record["has_ev"]),
        created_at=str(record["created_at"]),
        updated_at=str(record["updated_at"]),
    )


def _home_detail_from_record(
    record: dict[str, Any], latest_advice: dict[str, Any] | None
) -> HomeDetail:
    summary = _home_profile_from_record(record)
    return HomeDetail(
        **summary.model_dump(),
        ai_context=[str(item) for item in record["ai_context"]],
        latest_advice=latest_advice,
    )


def create_home(database_url: str, request: HomeCreateRequest) -> HomeDetail:
    home_record = {
        "id": new_id("home"),
        "name": request.name,
        "build_period": request.build_period.value,
        "home_size": request.home_size.value,
        "residents": request.residents.value,
        "heating_system": request.heating_system.value,
        "has_ev": request.has_ev,
        "ai_context": build_ai_context(request),
    }
    with connect(database_url) as connection:
        created = create_home_record(connection, home_record)
    return _home_detail_from_record(created, latest_advice=None)


def list_homes(database_url: str) -> list[HomeProfile]:
    with connect(database_url) as connection:
        records = list_home_records(connection)
    return [_home_profile_from_record(record) for record in records]


def get_home(database_url: str, home_id: str) -> HomeDetail:
    with connect(database_url) as connection:
        record = get_home_record(connection, home_id)
        if record is None:
            raise NotFoundError("Home profile was not found.")
        latest_advice = get_latest_advice(connection, home_id)
    return _home_detail_from_record(record, latest_advice=latest_advice)
