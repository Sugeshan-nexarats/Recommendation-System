
from __future__ import annotations
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.features.quality.abstract_quality_signal import AbstractQualitySignal

logger = logging.getLogger(__name__)

class QualitySignalRegistry:

    _registry: dict[str, "AbstractQualitySignal"] = {}

    @classmethod
    def register(
        cls, signal_cls: "type[AbstractQualitySignal]"
    ) -> "type[AbstractQualitySignal]":
        instance = signal_cls()
        name = instance.name

        if name in cls._registry:
            raise ValueError(f"Duplicate quality signal name '{name}'.")

        cls._registry[name] = instance
        return signal_cls

    @classmethod
    def all_signals(cls) -> list["AbstractQualitySignal"]:
        return list(cls._registry.values())

    @classmethod
    def signal_names(cls) -> list[str]:
        return list(cls._registry.keys())

    @classmethod
    def _reset(cls) -> None:
        cls._registry.clear()
