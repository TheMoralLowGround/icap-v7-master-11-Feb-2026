import re

_INVALID_IDENTIFIER_CHARS = re.compile(r"[^0-9A-Za-z_-]+")
_REPEATED_SEPARATORS = re.compile(r"[_-]{2,}")


def normalize_process_or_project_name(raw_name: str, *, max_length: int = 256) -> str:
    """Return a Qdrant-safe process name derived from arbitrary user input.

    The function trims whitespace, swaps any disallowed character for an
    underscore, collapses duplicated separators, strips leading/trailing
    separators, and enforces a maximum length. Raises ``ValueError`` if the
    result would be empty (e.g., the input only contained punctuation).
    """

    if raw_name is None:
        raise ValueError("Process name cannot be empty.")

    cleaned = raw_name.strip()
    if not cleaned:
        raise ValueError("Process name cannot be empty.")

    cleaned = _INVALID_IDENTIFIER_CHARS.sub("_", cleaned)
    cleaned = _REPEATED_SEPARATORS.sub("_", cleaned)
    cleaned = cleaned.strip("_-")

    if not cleaned:
        raise ValueError("Process name must contain at least one alphanumeric character.")

    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned



__all__ = ["normalize_process_name"]