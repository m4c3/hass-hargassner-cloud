from __future__ import annotations

import logging
import re

# Punkt 12: Logger-Filter zum Redacten sensibler Felder

# grobe Muster für JSON/Querystrings
_PATTERNS = [
    re.compile(
        r'("?(?:password|client_secret|access_token|token)"?\s*:\s*")([^"]+)(")',
        re.IGNORECASE,
    ),
    re.compile(
        r"((?:password|client_secret|access_token|token)=)([^&\s]+)", re.IGNORECASE
    ),
    re.compile(r"(Authorization:\s*Bearer\s+)([A-Za-z0-9._\-]+)", re.IGNORECASE),
]


class RedactSecretsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        redacted = msg
        for pattern in _PATTERNS:
            redacted = pattern.sub(
                r"\1***\3" if pattern.groups == 3 else r"\1***", redacted
            )
        record.msg = redacted
        record.args = ()
        return True
