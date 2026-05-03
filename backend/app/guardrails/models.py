from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class GuardrailSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    BLOCKED = "blocked"


class GuardrailEventType(StrEnum):
    PII_SCRUBBED = "pii_scrubbed"
    PROMPT_INJECTION_BLOCKED = "prompt_injection_blocked"
    OFF_TOPIC_WARNING = "off_topic_warning"
    OFF_TOPIC_BLOCKED = "off_topic_blocked"
    POST_VALIDATION_FAILED = "post_validation_failed"
    FALLBACK_USED = "fallback_used"
    PROVIDER_ERROR = "provider_error"


@dataclass(frozen=True)
class PIIResult:
    original_text: str
    scrubbed_text: str
    changed: bool
    entity_types: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RiskSignal:
    scanner: str
    reason: str
    severity: GuardrailSeverity
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GuardrailInputResult:
    original_message: str
    scrubbed_message: str
    source: str
    pii_changed: bool
    pii_entity_types: list[str]
