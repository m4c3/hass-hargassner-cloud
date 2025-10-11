from __future__ import annotations
import logging
import re

# Punkt 12: Logger-Filter zum Redacten sensibler Felder

_SECRET_KEYS = ("password", "client_secret", "access_token", "token", "authorization")

# grobe Muster für JSON/Querystrings
_PATTERNS = [
    re.compile(r'("?(?:password|client_secret|access_token|token)"?\s*:\s*")([^"]+)(")', re.IGNORECASE),
    re.compile(r'((?:password|client_secret|access_token|token)=)([^&\s]+)', re.IGNORECASE),
    re.compile(r'(Authorization:\s*Bearer\s+)([A-Za-z0-9._\-]+)', re.IGNORECASE),
]

class RedactSecretsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = str(record.getMessage())
            redacted = msg
            for pat in _PATTERNS:
                redacted = pat.sub(r"\1***\3" if pat.groups==3 else r"\1***", redacted)
            # Fallback: Schlüsselwörter hart ersetzen
            for key in _SECRET_KEYS:
                redacted = redacted.replace(key, f"{key}")
            record.msg = redacted
        except Exception:
            pass
        return True
