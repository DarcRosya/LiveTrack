from typing import Any


def strip_string(value: Any) -> Any:
    """Removes leading/trailing whitespace if the value is a string."""
    if isinstance(value, str):
        return value.strip()
    return value