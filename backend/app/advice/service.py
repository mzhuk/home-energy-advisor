from typing import Any

from app.advice.deterministic import build_deterministic_advice
from app.advice.models import AdviceRecord, AdviceResponse
from app.advice.repository import get_latest_advice as get_latest_advice_record
from app.advice.repository import save_advice
from app.core.errors import AdviceNotFoundError, NotFoundError
from app.core.settings import Settings
from app.db.connection import connect
from app.db.ids import new_id
from app.homes.repository import get_home as get_home_record
from app.homes.schemas import HomeProfile


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


def _advice_record_from_dict(record: dict[str, Any]) -> AdviceRecord:
    return AdviceRecord(
        id=str(record["id"]),
        home_id=str(record["home_id"]),
        summary=str(record["summary"]),
        areas=record["areas"],
        disclaimer=str(record["disclaimer"]),
        provider=str(record["provider"]),
        used_fallback=bool(record["used_fallback"]),
        created_at=str(record["created_at"]),
    )


def get_latest_advice(database_url: str, home_id: str) -> AdviceRecord:
    with connect(database_url) as connection:
        home = get_home_record(connection, home_id)
        if home is None:
            raise NotFoundError("Home profile was not found.")

        latest = get_latest_advice_record(connection, home_id)
        if latest is None:
            raise AdviceNotFoundError()

    return _advice_record_from_dict(latest)


def generate_advice(settings: Settings, home_id: str) -> AdviceRecord:
    with connect(settings.database_url) as connection:
        home_record = get_home_record(connection, home_id)
        if home_record is None:
            raise NotFoundError("Home profile was not found.")

        deterministic = build_deterministic_advice(
            _home_profile_from_record(home_record),
            ai_context=[str(item) for item in home_record["ai_context"]],
        )
        saved = save_advice(
            connection,
            _persisted_fallback_advice(
                home_id=home_id,
                provider=settings.llm_provider,
                advice=deterministic,
            ),
        )

    return _advice_record_from_dict(saved)


def _persisted_fallback_advice(
    *, home_id: str, provider: str, advice: AdviceResponse
) -> dict[str, Any]:
    return {
        "id": new_id("advice"),
        "home_id": home_id,
        "summary": advice.summary,
        "areas": [area.model_dump(mode="json") for area in advice.areas],
        "disclaimer": advice.disclaimer,
        "provider": provider,
        "used_fallback": True,
    }

