import re
from urllib.parse import urlparse, urlunparse

MAX_URL_LENGTH = 2048
SHORT_CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{1,10}$")


def normalize_and_validate_url(raw):
    if not isinstance(raw, str):
        return None, "URL must be a string"

    candidate = raw.strip()
    if not candidate:
        return None, "URL is required"
    if len(candidate) > MAX_URL_LENGTH:
        return None, f"URL exceeds maximum length of {MAX_URL_LENGTH} characters"

    if "://" not in candidate:
        candidate = "https://" + candidate

    parsed = urlparse(candidate)
    if parsed.scheme not in ("http", "https"):
        return None, "Only http and https URLs are supported"
    if not parsed.netloc or "." not in parsed.netloc:
        return None, "Invalid URL: missing or malformed host"

    normalized = urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )
    return normalized, None


def is_valid_short_code(code):
    return isinstance(code, str) and bool(SHORT_CODE_PATTERN.fullmatch(code))
