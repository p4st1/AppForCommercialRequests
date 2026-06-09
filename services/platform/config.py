from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config import Config
from services.platform.constants import (
    DEFAULT_PLATFORM_LIMIT,
    DEFAULT_PLATFORM_MAX_ITEMS,
    DEFAULT_PLATFORM_TIMEOUT,
)


@dataclass(frozen=True)
class PlatformLoadConfig:
    default_limit: int = DEFAULT_PLATFORM_LIMIT
    max_items: int = DEFAULT_PLATFORM_MAX_ITEMS
    timeout: float | tuple[float, float] = DEFAULT_PLATFORM_TIMEOUT

    @classmethod
    def from_config(cls, raw_config: dict[str, Any] | None = None) -> "PlatformLoadConfig":
        config = raw_config if isinstance(raw_config, dict) else Config.config
        if not isinstance(config, dict):
            config = {}

        platform_config = config.get("platformTradeLoad")
        if not isinstance(platform_config, dict):
            platform_config = {}

        default_limit = _coerce_positive_int(
            platform_config.get("default_limit", config.get("platformDefaultLimit")),
            DEFAULT_PLATFORM_LIMIT,
        )
        max_items = _coerce_non_negative_int(
            platform_config.get("max_items", config.get("platformMaxItems")),
            DEFAULT_PLATFORM_MAX_ITEMS,
        )
        timeout = _coerce_timeout(
            platform_config.get("timeout", config.get("platformTimeout")),
            DEFAULT_PLATFORM_TIMEOUT,
        )
        return cls(default_limit=default_limit, max_items=max_items, timeout=timeout)


def _coerce_positive_int(raw_value: Any, default: int) -> int:
    try:
        value = int(float(str(raw_value).strip().replace(",", ".")))
    except (TypeError, ValueError):
        value = default
    return max(1, value)


def _coerce_non_negative_int(raw_value: Any, default: int) -> int:
    try:
        value = int(float(str(raw_value).strip().replace(",", ".")))
    except (TypeError, ValueError):
        value = default
    return max(0, value)


def _coerce_timeout(
    raw_value: Any,
    default: float | tuple[float, float],
) -> float | tuple[float, float]:
    if isinstance(raw_value, (list, tuple)) and len(raw_value) == 2:
        try:
            connect_timeout = float(raw_value[0])
            read_timeout = float(raw_value[1])
        except (TypeError, ValueError):
            return default
        return (max(0.1, connect_timeout), max(0.1, read_timeout))

    try:
        timeout = float(raw_value)
    except (TypeError, ValueError):
        return default
    return max(0.1, timeout)
