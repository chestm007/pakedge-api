"""Unified parser for PakEdge API response formats."""

from __future__ import annotations

import re
from typing import Any


def _normalize_obj(raw: str) -> str:
    """Convert PakEdge's unquoted-key object to valid Python dict literal.

    Input:  {port:1,linkstatus:0,state:1,pvid:1}
    Output: {"port":1,"linkstatus":0,"state":1,"pvid":1}
    """
    # Strip trailing comma inside braces
    if raw.endswith(","):
        raw = raw[:-1]
    # Wrap bare word keys in double quotes
    return re.sub(r"(?<=\{|\,)\s*(\w+)\s*:", r' "\1":', raw)


def parse_single_object(raw: str) -> dict[str, Any]:
    """Parse a single unquoted-key object: {key:"val",key2:0,}

    Returns dict or empty dict on failure.
    """
    raw = raw.strip()
    if not raw or not (raw.startswith("{") and raw.endswith("}")):
        return {}
    normalized = _normalize_obj(raw)
    try:
        return eval(normalized)  # noqa: S307 — trusted device data
    except (SyntaxError, ValueError):
        return {}


def parse_pipe_array(raw: str) -> list[dict[str, Any]]:
    """Parse pipe-delimited array: {..}|{..}|...|0

    Returns list of dicts, skipping non-object parts and trailing footer.
    """
    raw = raw.strip()
    if not raw:
        return []

    parts = raw.split("|")
    result: list[dict[str, Any]] = []

    for part in parts:
        part = part.strip()
        if not part or part == "0":
            continue
        if not (part.startswith("{") and part.endswith("}")):
            continue
        obj = parse_single_object(part)
        if obj:
            result.append(obj)

    return result


def parse_quoted_object(raw: str) -> dict[str, Any]:
    """Parse a quoted single object: '{key:"val",}'

    Returns dict or empty dict on failure.
    """
    raw = raw.strip()
    if not (raw.startswith("'") and raw.endswith("'")):
        return parse_single_object(raw)
    inner = raw[1:-1]
    return parse_single_object(inner)


def parse_response(raw: str) -> dict[str, Any] | list[dict[str, Any]]:
    """Auto-detect and parse PakEdge response format.

    Returns:
        dict for single objects, list for pipe-delimited arrays,
        or the raw string for scalars like "20".
    """
    raw = raw.strip()
    if not raw:
        return {}

    # Check for pipe-delimited array
    if "|" in raw and "{" in raw:
        result = parse_pipe_array(raw)
        return result if result else {}

    # Check for quoted object
    if raw.startswith("'") and raw.endswith("'"):
        return parse_quoted_object(raw)

    # Try single object
    if raw.startswith("{") and raw.endswith("}"):
        return parse_single_object(raw)

    # Scalar
    return raw
