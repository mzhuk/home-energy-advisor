import re
from os import getenv
from typing import Any, cast

from app.core.errors import PIIScrubFailedError
from app.guardrails.models import PIIResult

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
ADDRESS_RE = re.compile(
    r"\b\d{1,6}\s+[A-Z][A-Za-z0-9.'-]*(?:\s+[A-Z][A-Za-z0-9.'-]*){0,4}\s+"
    r"(?:Street|St|Road|Rd|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way)\b",
    re.IGNORECASE,
)
PERSON_CONTEXT_RE = re.compile(
    r"\b(?P<label>"
    r"(?:my\s+)?(?:full\s+)?name\s+is|"
    r"(?:my\s+)?first\s+name\s+is|"
    r"(?:my\s+)?last\s+name\s+is|"
    r"(?:my\s+)?surname\s+is"
    r")\s+(?P<name>[A-Z][a-z]+(?:[-'][A-Z][a-z]+)?(?:\s+[A-Z][a-z]+(?:[-'][A-Z][a-z]+)?){0,2})\b",
    re.IGNORECASE,
)


class PIIScrubber:
    def scrub(self, text: str) -> PIIResult:
        try:
            return self._scrub_with_fallback_patterns(text)
        except Exception as exc:
            raise PIIScrubFailedError() from exc

    def _scrub_with_fallback_patterns(self, text: str) -> PIIResult:
        scrubbed = text
        entity_types: list[str] = []

        scrubbed, email_count = EMAIL_RE.subn("[EMAIL_ADDRESS]", scrubbed)
        if email_count:
            entity_types.append("EMAIL_ADDRESS")

        scrubbed, phone_count = PHONE_RE.subn("[PHONE_NUMBER]", scrubbed)
        if phone_count:
            entity_types.append("PHONE_NUMBER")

        scrubbed, address_count = ADDRESS_RE.subn("[ADDRESS]", scrubbed)
        if address_count:
            entity_types.append("ADDRESS")

        def replace_person(match: re.Match[str]) -> str:
            return f"{match.group('label')} [PERSON]"

        scrubbed, person_count = PERSON_CONTEXT_RE.subn(replace_person, scrubbed)
        if person_count:
            entity_types.append("PERSON")

        presidio_result = _try_presidio_scrub(scrubbed)
        if presidio_result.changed:
            scrubbed = presidio_result.scrubbed_text
            entity_types.extend(presidio_result.entity_types)

        return PIIResult(
            original_text=text,
            scrubbed_text=scrubbed,
            changed=scrubbed != text,
            entity_types=sorted(set(entity_types)),
        )


def _try_presidio_scrub(text: str) -> PIIResult:
    if getenv("ENABLE_PRESIDIO_RUNTIME", "").lower() not in {"1", "true", "yes"}:
        return PIIResult(text, text, changed=False)

    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine
    except Exception:
        return PIIResult(text, text, changed=False)

    try:
        analyzer = AnalyzerEngine()
        results = analyzer.analyze(
            text=text,
            language="en",
            entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "PERSON", "LOCATION"],
        )
        if not results:
            return PIIResult(text, text, changed=False)
        anonymized = AnonymizerEngine().anonymize(
            text=text,
            analyzer_results=cast(Any, results),
        )
    except Exception:
        return PIIResult(text, text, changed=False)

    return PIIResult(
        original_text=text,
        scrubbed_text=anonymized.text,
        changed=anonymized.text != text,
        entity_types=sorted({result.entity_type for result in results}),
    )
