import json

from pydantic import ValidationError

from app.advice.models import AdviceResponse, AreaId
from app.core.errors import LLMBadResponseError
from app.guardrails.scanners import ScannerSuite
from app.homes.schemas import HomeProfile

CORE_AREA_IDS = {AreaId.SOLAR, AreaId.BATTERY, AreaId.HEAT_PUMP, AreaId.SMART_CONTROLS}


class ResponseValidator:
    def validate_advice(self, raw_text: str, *, home: HomeProfile) -> AdviceResponse:
        json_text = extract_json_object(raw_text)
        try:
            advice = AdviceResponse.model_validate_json(json_text)
        except ValidationError as exc:
            raise LLMBadResponseError(
                "The model returned advice that does not match the schema."
            ) from exc
        self._validate_area_contract(advice, home=home)
        return advice

    def validate_chat_response(self, raw_text: str) -> str:
        text = raw_text.strip()
        if not text:
            raise LLMBadResponseError("The model returned an empty chat response.")
        if ScannerSuite().scan_output(text):
            raise LLMBadResponseError("The model returned a response outside the allowed scope.")
        return text

    def _validate_area_contract(self, advice: AdviceResponse, *, home: HomeProfile) -> None:
        area_ids = [area.area_id for area in advice.areas]
        if len(area_ids) != len(set(area_ids)):
            raise LLMBadResponseError("The model returned duplicate advice areas.")
        missing_core = CORE_AREA_IDS.difference(area_ids)
        if missing_core:
            raise LLMBadResponseError("The model omitted required advice areas.")
        if AreaId.EV_CHARGING in area_ids and not home.has_ev:
            raise LLMBadResponseError("The model returned EV charging advice for a non-EV profile.")
        if home.has_ev and AreaId.EV_CHARGING not in area_ids:
            raise LLMBadResponseError("The model omitted EV charging advice for an EV profile.")


def extract_json_object(raw_text: str) -> str:
    text = raw_text.strip()
    if not text:
        raise LLMBadResponseError("The model returned an empty response.")
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise LLMBadResponseError(
                "The model response did not contain a JSON object."
            ) from None
        candidate = text[start : end + 1]
        try:
            json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise LLMBadResponseError("The model response did not contain valid JSON.") from exc
        return candidate
