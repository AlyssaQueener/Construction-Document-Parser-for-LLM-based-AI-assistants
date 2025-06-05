"""This module abstracts utilities for processing of the extracted values."""

from logging import getLogger
import re
from typing import Any
from typing import Dict
from typing import Optional


logger = getLogger(__name__)


def _apply_grouping(settings: Dict[str, Any], result: Any) -> Optional[Any]:
    """Apply grouping to the extracted values."""
    if "group" in settings:
        result = list(filter(None, result))
        if result:
            if settings["group"] == "sum":
                result = sum(result)
            elif settings["group"] == "min":
                result = min(result)
            elif settings["group"] == "max":
                result = max(result)
            elif settings["group"] == "first":
                result = result[0]
            elif settings["group"] == "last":
                result = result[-1]
            elif settings["group"] == "join":
                joined = " ".join(str(v) for v in result) if result else ""
                result = [joined]
            else:
                logger.warning("Unsupported grouping method: %s", settings["group"])
                return None
    return result
import re

def clean_broken_lines(text):
    lines = text.splitlines()
    cleaned_lines = []
    buffer = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue  # skip empty lines

        # If this is the start of a new line item
        if re.match(r"^\d+\s", stripped):  # starts with item number
            if buffer:
                cleaned_lines.append(buffer.strip())
            buffer = stripped
        # If this looks like a continuation line with unit + qty + rate + amount
        elif re.match(r"^\s*(m³|m²|ml|m3|m|L\.S\.|Pce)[\s\d,.]+$", stripped):
            buffer += " " + stripped
        else:
            buffer += " " + stripped

    if buffer:
        cleaned_lines.append(buffer.strip())

    print("Cleaned lines:")
    for line in cleaned_lines:
        print(line)

    return "\n".join(cleaned_lines)
