import re
from collections.abc import Iterable

from app.guardrails.models import GuardrailSeverity, RiskSignal

PROMPT_INJECTION_PATTERNS = (
    re.compile(r"\bignore (?:all )?(?:previous|prior|above) instructions\b", re.IGNORECASE),
    re.compile(r"\breveal (?:your )?(?:system|developer) prompt\b", re.IGNORECASE),
    re.compile(r"\bprint hidden developer message\b", re.IGNORECASE),
    re.compile(r"\bact as a different assistant\b", re.IGNORECASE),
    re.compile(r"\bdisable (?:all )?safety rules\b", re.IGNORECASE),
    re.compile(r"\bexfiltrate conversation context\b", re.IGNORECASE),
)

OFF_TOPIC_PATTERNS = (
    re.compile(r"\b(?:stock|crypto|lawsuit|divorce|diagnosis|medicine|recipe)\b", re.IGNORECASE),
    re.compile(r"\b(?:buy|sell) (?:stocks|crypto|bitcoin)\b", re.IGNORECASE),
)

HOME_ENERGY_TERMS = (
    "solar",
    "panel",
    "battery",
    "storage",
    "heat pump",
    "heating",
    "thermostat",
    "smart",
    "monitor",
    "energy",
    "electric",
    "ev",
    "charging",
    "charger",
    "roof",
    "home",
    "power",
    "insulation",
    "wiring",
)

PROMPT_LEAK_PATTERNS = (
    re.compile(r"\bsystem prompt\b", re.IGNORECASE),
    re.compile(r"\bhidden developer message\b", re.IGNORECASE),
    re.compile(r"\bconfidential instructions\b", re.IGNORECASE),
)

UNSAFE_INSTALLATION_PATTERNS = (
    re.compile(r"\b(?:open|remove)\s+(?:the\s+)?(?:breaker|electrical panel)\b", re.IGNORECASE),
    re.compile(
        r"\bwire\s+(?:the\s+)?(?:inverter|charger|battery|panel)\s+yourself\b",
        re.IGNORECASE,
    ),
    re.compile(r"\broof installation step[- ]by[- ]step\b", re.IGNORECASE),
    re.compile(r"\bhandle refrigerant\b", re.IGNORECASE),
)

EXACT_ROI_PATTERNS = (
    re.compile(r"\bpayback (?:period )?(?:is|will be)\s+\d+(?:\.\d+)?\s+years?\b", re.IGNORECASE),
    re.compile(
        r"\bsave\s+\$?\d+(?:,\d{3})*(?:\.\d+)?\s+(?:per|a)\s+(?:month|year)\b",
        re.IGNORECASE,
    ),
)


class ScannerSuite:
    def scan_input(self, message: str) -> list[RiskSignal]:
        signals: list[RiskSignal] = []
        signals.extend(
            _signals_for_patterns("prompt_injection", message, PROMPT_INJECTION_PATTERNS)
        )
        signals.extend(_signals_for_patterns("ban_topics", message, OFF_TOPIC_PATTERNS))
        if _looks_off_topic(message):
            signals.append(
                RiskSignal(
                    scanner="topic_relevance",
                    reason="Message does not appear related to home energy advice.",
                    severity=GuardrailSeverity.BLOCKED,
                )
            )
        return signals

    def scan_output(self, text: str) -> list[RiskSignal]:
        signals: list[RiskSignal] = []
        signals.extend(_signals_for_patterns("prompt_leakage", text, PROMPT_LEAK_PATTERNS))
        signals.extend(
            _signals_for_patterns("unsafe_installation", text, UNSAFE_INSTALLATION_PATTERNS)
        )
        signals.extend(_signals_for_patterns("exact_roi_claim", text, EXACT_ROI_PATTERNS))
        signals.extend(_signals_for_patterns("ban_topics", text, OFF_TOPIC_PATTERNS))
        return signals


def _signals_for_patterns(
    scanner: str, text: str, patterns: Iterable[re.Pattern[str]]
) -> list[RiskSignal]:
    return [
        RiskSignal(
            scanner=scanner,
            reason=f"{scanner} pattern matched.",
            severity=GuardrailSeverity.BLOCKED,
        )
        for pattern in patterns
        if pattern.search(text)
    ]


def _looks_off_topic(message: str) -> bool:
    normalized = message.lower()
    if len(normalized.split()) <= 3:
        return False
    return not any(term in normalized for term in HOME_ENERGY_TERMS)
