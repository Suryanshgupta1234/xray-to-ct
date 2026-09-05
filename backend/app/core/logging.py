"""
Structured Logging Module.
Enforces structured JSON or standardized log output, sanitizes sensitive
credentials/tokens/PHI, and captures request IDs and latency metrics.
"""

import sys
import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict


class SafeJsonFormatter(logging.Formatter):
    """Formats log records as JSON, filtering passwords, tokens, and PHI tags."""

    REDACTED = "[REDACTED]"
    SENSITIVE_KEYS = {
        "password", "hashed_password", "token", "jwt", "authorization",
        "patientname", "patient_name", "patientid", "patient_id", "secret"
    }

    def format(self, record: logging.LogRecord) -> str:
        data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include contextual extras if present
        for key in ("request_id", "user_id", "endpoint", "method", "status_code",
                    "inference_duration_ms", "model_version"):
            if hasattr(record, key):
                data[key] = getattr(record, key)

        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)

        # Sanitize sensitive fields
        sanitized = self._sanitize_dict(data)
        return json.dumps(sanitized)

    def _sanitize_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        clean = {}
        for k, v in d.items():
            if any(s in k.lower() for s in self.SENSITIVE_KEYS):
                clean[k] = self.REDACTED
            elif isinstance(v, dict):
                clean[k] = self._sanitize_dict(v)
            else:
                clean[k] = v
        return clean


def setup_logger(name: str = "xray_ct_api") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(SafeJsonFormatter())
        logger.addHandler(handler)

    return logger


logger = setup_logger()
