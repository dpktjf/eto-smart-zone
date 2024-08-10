"""Util functions for ETO."""

from typing import Any

OPTION_DEFAULTS = {}


def build_data_and_options(
    combined_data: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Split combined data and options."""
    data = {k: v for k, v in combined_data.items() if k not in OPTION_DEFAULTS}
    options = {
        option: combined_data.get(option, default)
        for option, default in OPTION_DEFAULTS.items()
    }
    return (data, options)
