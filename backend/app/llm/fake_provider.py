import json
from collections.abc import Sequence
from typing import Any

from app.advice.models import AdviceResponse, AreaAdvice, AreaId, Priority
from app.llm.client import ChatSource, LLMMessage

DEMO_NOTE = (
    "Demo note: for demo purposes, this response is limited to predefined advice for this category."
)


class FakeLLMClient:
    def generate_advice(
        self, messages: Sequence[LLMMessage], response_schema: dict[str, Any]
    ) -> str:
        if messages:
            try:
                advice = AdviceResponse.model_validate_json(messages[-1].content)
            except ValueError:
                advice = _default_advice()
        else:
            advice = _default_advice()

        _ = response_schema
        advice.disclaimer = f"{advice.disclaimer} {DEMO_NOTE}"
        return advice.model_dump_json()

    def chat(self, messages: Sequence[LLMMessage], *, source: ChatSource = "global") -> str:
        return f"{_CHAT_RESPONSES[source]}\n\n{DEMO_NOTE}"


def _default_advice() -> AdviceResponse:
    return AdviceResponse(
        summary=(
            "Start with a practical energy baseline, then prioritize solar readiness, storage "
            "fit, heat pump planning, and smart controls around the profile."
        ),
        areas=[
            AreaAdvice(
                area_id=AreaId.SOLAR,
                title="Solar panels",
                priority=Priority.HIGH,
                insight=(
                    "Use measured electricity demand and future electrification plans before "
                    "settling on panel count or inverter capacity."
                ),
                first_step="Prepare annual usage and roof constraints before requesting quotes.",
                default_prompt=(
                    "Given my home profile, what are the best improvements for my solar setup?"
                ),
                suggested_questions=[
                    "How should I size solar for this profile?",
                    "What roof details should I confirm first?",
                ],
            ),
            AreaAdvice(
                area_id=AreaId.BATTERY,
                title="Home power station",
                priority=Priority.MEDIUM,
                insight=(
                    "Storage is most useful when it absorbs real solar surplus or manages "
                    "evening demand."
                ),
                first_step="Review hourly load data before choosing battery capacity.",
                default_prompt=(
                    "Given my home profile, would a home battery or power station be useful?"
                ),
                suggested_questions=[
                    "Should I add storage now or later?",
                    "What data proves a battery is useful?",
                ],
            ),
            AreaAdvice(
                area_id=AreaId.HEAT_PUMP,
                title="Heat pump heating",
                priority=Priority.HIGH,
                insight=(
                    "Heating electrification should be planned with load calculations, comfort "
                    "needs, and solar support in mind."
                ),
                first_step="Schedule a professional heat-load assessment.",
                default_prompt=(
                    "Given my home profile, what should I improve around heat pump heating?"
                ),
                suggested_questions=[
                    "What should a heat pump assessment include?",
                    "How should controls support heating efficiency?",
                ],
            ),
            AreaAdvice(
                area_id=AreaId.SMART_CONTROLS,
                title="Smart controls",
                priority=Priority.HIGH,
                insight=(
                    "Monitoring and schedules help coordinate solar, storage, heating, and "
                    "flexible loads."
                ),
                first_step="Start with one dashboard for production, load, and heating runtime.",
                default_prompt=(
                    "Given my home profile, how should smart controls monitor and operate my home?"
                ),
                suggested_questions=[
                    "Which metrics should I monitor first?",
                    "How can controls shift demand to solar hours?",
                ],
            ),
        ],
        disclaimer=(
            "This is directional planning advice, not a substitute for professional electrical, "
            "roofing, HVAC, or code compliance assessment."
        ),
    )


_CHAT_RESPONSES: dict[ChatSource, str] = {
    "global": (
        "For the whole home, prioritize a measured baseline first: current electricity demand, "
        "heating load, solar potential, and which loads can be shifted automatically."
    ),
    "solar": (
        "For solar, start by matching panel layout to real roof constraints and future electric "
        "loads such as heat pump heating or EV charging."
    ),
    "battery": (
        "For storage, check whether the home has enough evening demand or solar surplus before "
        "choosing a battery size."
    ),
    "heat_pump": (
        "For heat pumps, confirm heat-load calculations, distribution readiness, controls, and "
        "maintenance before changing equipment."
    ),
    "smart_controls": (
        "For smart controls, monitor solar production, household load, heating runtime, and "
        "flexible schedules in one place."
    ),
    "ev_charging": (
        "For EV charging, coordinate charger settings with solar production, household peaks, and "
        "any future battery strategy."
    ),
}


def fake_advice_as_dict() -> dict[str, Any]:
    return json.loads(FakeLLMClient().generate_advice([], {}))
