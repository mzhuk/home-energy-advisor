from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BuildPeriod(StrEnum):
    PRE_1978 = "pre_1978"
    Y1980_2000 = "y1980_2000"
    POST_2000 = "post_2000"
    IN_PROGRESS = "in_progress"


class HomeSize(StrEnum):
    UNDER_100 = "under_100"
    Y100_200 = "y100_200"
    OVER_200 = "over_200"


class Residents(StrEnum):
    ONE_TWO = "one_two"
    THREE_FOUR = "three_four"
    FIVE_PLUS = "five_plus"


class HeatingSystem(StrEnum):
    GAS = "gas"
    HEAT_PUMP = "heat_pump"
    OTHER_UNKNOWN = "other_unknown"


class HomeCreateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Main house",
                "build_period": "pre_1978",
                "home_size": "y100_200",
                "residents": "three_four",
                "heating_system": "gas",
                "has_ev": True,
            }
        }
    )

    name: str = Field(min_length=1, max_length=80)
    build_period: BuildPeriod
    home_size: HomeSize
    residents: Residents
    heating_system: HeatingSystem
    has_ev: bool

    @field_validator("name")
    @classmethod
    def trim_and_validate_name(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            msg = "Home name cannot be empty."
            raise ValueError(msg)
        if len(trimmed) > 80:
            msg = "Home name must be under 80 characters."
            raise ValueError(msg)
        return trimmed


class HomeProfile(BaseModel):
    id: str
    name: str
    build_period: BuildPeriod
    home_size: HomeSize
    residents: Residents
    heating_system: HeatingSystem
    has_ev: bool
    created_at: str
    updated_at: str


class HomeDetail(HomeProfile):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "home_abc123",
                "name": "Main house",
                "build_period": "pre_1978",
                "home_size": "y100_200",
                "residents": "three_four",
                "heating_system": "gas",
                "has_ev": True,
                "ai_context": [
                    "Treat the home as likely to have weaker baseline efficiency and higher "
                    "heating demand. Prioritize practical heat pump readiness, smart heating "
                    "control, and realistic expectations for solar-plus-storage benefits. "
                    "Mention insulation only as supporting context for heat pump performance."
                ],
                "latest_advice": None,
                "created_at": "2026-05-02T10:00:00+00:00",
                "updated_at": "2026-05-02T10:00:00+00:00",
            }
        }
    )

    ai_context: list[str]
    latest_advice: dict[str, Any] | None = None
