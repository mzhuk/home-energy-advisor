from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AreaId(StrEnum):
    SOLAR = "solar"
    BATTERY = "battery"
    HEAT_PUMP = "heat_pump"
    SMART_CONTROLS = "smart_controls"
    EV_CHARGING = "ev_charging"


class Priority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AreaAdvice(BaseModel):
    area_id: AreaId
    title: str
    priority: Priority
    insight: str
    first_step: str
    default_prompt: str
    suggested_questions: list[str] = Field(min_length=2, max_length=3)


class AdviceResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "summary": (
                    "Start with heat pump readiness and smart controls, then size solar and "
                    "storage around the electrified load profile."
                ),
                "areas": [
                    {
                        "area_id": "heat_pump",
                        "title": "Heat pump readiness",
                        "priority": "high",
                        "insight": "Gas heating makes electrification the biggest planning lever.",
                        "first_step": "Book a heat-load assessment before choosing equipment.",
                        "default_prompt": (
                            "Given my home profile, what should I check before moving from gas "
                            "heating to a heat pump?"
                        ),
                        "suggested_questions": [
                            "What should a heat pump readiness assessment include?",
                            "How should solar planning change if I electrify heating?",
                        ],
                    }
                ],
                "disclaimer": (
                    "This is directional planning advice, not a substitute for professional "
                    "electrical, roofing, HVAC, or code compliance assessment."
                ),
            }
        }
    )

    summary: str
    areas: list[AreaAdvice]
    disclaimer: str


class AdviceRecord(AdviceResponse):
    id: str
    home_id: str
    provider: str
    used_fallback: bool
    created_at: str
