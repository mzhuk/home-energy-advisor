import sqlite3

from app.core.errors import OffTopicBlockedError, PromptInjectionBlockedError
from app.guardrails.audit import record_audit_event
from app.guardrails.models import (
    GuardrailEventType,
    GuardrailInputResult,
    GuardrailSeverity,
    RiskSignal,
)
from app.guardrails.pii import PIIScrubber
from app.guardrails.scanners import ScannerSuite
from app.homes.schemas import HomeProfile

ALLOWED_SOURCES = {"global", "solar", "battery", "heat_pump", "smart_controls", "ev_charging"}
MAX_MESSAGE_LENGTH = 2000


class GuardrailPipeline:
    def __init__(
        self,
        *,
        connection: sqlite3.Connection | None = None,
        pii_scrubber: PIIScrubber | None = None,
        scanners: ScannerSuite | None = None,
    ) -> None:
        self._connection = connection
        self._pii_scrubber = pii_scrubber or PIIScrubber()
        self._scanners = scanners or ScannerSuite()

    def run_input_hooks(self, home: HomeProfile, source: str, message: str) -> GuardrailInputResult:
        normalized_source = self._validate_source(home, source, message)
        stripped_message = message.strip()
        if not stripped_message or len(stripped_message) > MAX_MESSAGE_LENGTH:
            raise OffTopicBlockedError(
                "Please send a focused home energy question under 2000 characters."
            )

        signals = self._scanners.scan_input(stripped_message)
        self._raise_for_input_signals(home, normalized_source, stripped_message, signals)

        pii_result = self._pii_scrubber.scrub(stripped_message)
        if pii_result.changed:
            self._audit(
                home,
                event_type=GuardrailEventType.PII_SCRUBBED,
                source=normalized_source,
                severity=GuardrailSeverity.INFO,
                original_text=stripped_message,
                details={"entity_types": pii_result.entity_types},
            )

        return GuardrailInputResult(
            original_message=stripped_message,
            scrubbed_message=pii_result.scrubbed_text,
            source=normalized_source,
            pii_changed=pii_result.changed,
            pii_entity_types=pii_result.entity_types,
        )

    def run_output_hooks(self, home: HomeProfile, source: str, text: str) -> str:
        normalized_source = self._validate_source(home, source, text)
        signals = self._scanners.scan_output(text)
        if not signals:
            return text

        self._audit(
            home,
            event_type=GuardrailEventType.POST_VALIDATION_FAILED,
            source=normalized_source,
            severity=GuardrailSeverity.BLOCKED,
            original_text=text,
            details={"signals": [_signal_details(signal) for signal in signals]},
        )
        if any(signal.scanner == "prompt_leakage" for signal in signals):
            raise PromptInjectionBlockedError("The advisor response could not be returned safely.")
        raise OffTopicBlockedError("The advisor response moved outside the allowed energy scope.")

    def record_fallback_used(
        self, home: HomeProfile, source: str, *, reason: str, original_text: str | None = None
    ) -> None:
        self._audit(
            home,
            event_type=GuardrailEventType.FALLBACK_USED,
            source=source,
            severity=GuardrailSeverity.WARNING,
            original_text=original_text,
            details={"reason": reason},
        )

    def _validate_source(self, home: HomeProfile, source: str, original_text: str) -> str:
        if source not in ALLOWED_SOURCES:
            raise OffTopicBlockedError("Unknown home advice source.")
        if source == "ev_charging" and not home.has_ev:
            self._audit(
                home,
                event_type=GuardrailEventType.OFF_TOPIC_BLOCKED,
                source=source,
                severity=GuardrailSeverity.BLOCKED,
                original_text=original_text,
                details={"reason": "ev_source_without_ev"},
            )
            raise OffTopicBlockedError(
                "EV charging advice is only available for EV owner profiles."
            )
        return source

    def _raise_for_input_signals(
        self, home: HomeProfile, source: str, message: str, signals: list[RiskSignal]
    ) -> None:
        if not signals:
            return

        event_type = GuardrailEventType.OFF_TOPIC_BLOCKED
        if any(signal.scanner == "prompt_injection" for signal in signals):
            event_type = GuardrailEventType.PROMPT_INJECTION_BLOCKED

        self._audit(
            home,
            event_type=event_type,
            source=source,
            severity=GuardrailSeverity.BLOCKED,
            original_text=message,
            details={"signals": [_signal_details(signal) for signal in signals]},
        )
        if event_type == GuardrailEventType.PROMPT_INJECTION_BLOCKED:
            raise PromptInjectionBlockedError()
        raise OffTopicBlockedError()

    def _audit(
        self,
        home: HomeProfile,
        *,
        event_type: GuardrailEventType,
        source: str,
        severity: GuardrailSeverity,
        original_text: str | None,
        details: dict[str, object],
    ) -> None:
        if self._connection is None:
            return
        record_audit_event(
            self._connection,
            home_id=home.id,
            event_type=event_type,
            source=source,
            severity=severity,
            original_text=original_text,
            details=details,
        )


def _signal_details(signal: RiskSignal) -> dict[str, object]:
    return {
        "scanner": signal.scanner,
        "reason": signal.reason,
        "severity": signal.severity.value,
        "details": signal.details,
    }
