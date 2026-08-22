"""
RelationshipSignalRegistry — self-registering plugin hub for relationship signals.

Mirrors the design of FeatureRegistry (module-level decorator triggers
registration at import time).  RelationshipFeature iterates the registry
at request time without knowing which specific signal classes are active.

Auto-discovery:
    1. Each signal class is decorated with @RelationshipSignalRegistry.register.
    2. app/features/relationship/signals/__init__.py imports all signal modules,
       triggering registration.
    3. RelationshipFeature imports that __init__.py at module level so
       all signals are registered before any request is processed.

Adding a new signal:
    a. Create app/features/relationship/signals/my_signal.py, decorate the class.
    b. Add one import line to signals/__init__.py.
    RelationshipFeature, this registry, and all other signals — untouched.

Thread-safety:
    The registry dict is populated once at startup (import time) and is
    read-only at request time.  No locks are needed.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.features.relationship.abstract_relationship_signal import (
        AbstractRelationshipSignal,
    )

logger = logging.getLogger(__name__)


class RelationshipSignalRegistry:
    """
    Central registry of all active relationship signal plugins.

    Signals self-register via @RelationshipSignalRegistry.register.
    RelationshipFeature calls registry.all_signals() to iterate them.
    """

    # Populated at import time via @register.  Read-only at request time.
    _registry: dict[str, "AbstractRelationshipSignal"] = {}

    # ------------------------------------------------------------------
    # Plugin decorator
    # ------------------------------------------------------------------

    @classmethod
    def register(
        cls, signal_cls: "type[AbstractRelationshipSignal]"
    ) -> "type[AbstractRelationshipSignal]":
        """
        Class decorator that instantiates and registers a relationship signal.

        Usage::

            @RelationshipSignalRegistry.register
            class MySignal(AbstractRelationshipSignal):
                ...

        Raises:
            ValueError: On duplicate signal names (caught at startup, not runtime).
        """
        instance: "AbstractRelationshipSignal" = signal_cls()
        name = instance.name

        if name in cls._registry:
            raise ValueError(
                f"RelationshipSignalRegistry: duplicate signal name '{name}'. "
                f"Existing: {type(cls._registry[name]).__name__}, "
                f"Conflicting: {signal_cls.__name__}."
            )

        cls._registry[name] = instance
        logger.debug("RelationshipSignalRegistry: registered signal '%s'", name)
        return signal_cls

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def all_signals(cls) -> list["AbstractRelationshipSignal"]:
        """Return all registered signal instances in registration order."""
        return list(cls._registry.values())

    @classmethod
    def signal_names(cls) -> list[str]:
        """Return canonical names of all registered signals."""
        return list(cls._registry.keys())

    @classmethod
    def _reset(cls) -> None:
        """
        Clear all registered signals.

        Intended for use in unit tests only.  Never call in production code.
        """
        cls._registry.clear()
