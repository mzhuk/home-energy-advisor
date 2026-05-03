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
    "air sealing",
    "appliance",
    "attic",
    "backup",
    "battery",
    "bill",
    "boiler",
    "carbon",
    "charger",
    "charging",
    "comfort",
    "consumption",
    "cooling",
    "demand",
    "door",
    "efficiency",
    "efficient",
    "electric",
    "electrification",
    "emissions",
    "energy",
    "ev",
    "furnace",
    "garage",
    "grid",
    "heat pump",
    "heating",
    "home",
    "hot water",
    "hvac",
    "insulation",
    "inverter",
    "led",
    "lighting",
    "load",
    "meter",
    "microinverter",
    "monitor",
    "outage",
    "panel",
    "power",
    "radiator",
    "renewable",
    "retrofit",
    "roof",
    "schedule",
    "smart",
    "solar",
    "storage",
    "tariff",
    "temperature",
    "thermostat",
    "time-of-use",
    "usage",
    "utility",
    "ventilation",
    "water heater",
    "weatherization",
    "window",
    "wiring",
)

PROMPT_LEAK_PATTERNS = (
    re.compile(r"\bsystem prompt\b", re.IGNORECASE),
    re.compile(r"\bhidden developer message\b", re.IGNORECASE),
    re.compile(r"\bconfidential instructions\b", re.IGNORECASE),
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
                    severity=GuardrailSeverity.WARNING,
                )
            )
        return signals

    def scan_output(self, text: str) -> list[RiskSignal]:
        signals: list[RiskSignal] = []
        signals.extend(_signals_for_patterns("prompt_leakage", text, PROMPT_LEAK_PATTERNS))
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
