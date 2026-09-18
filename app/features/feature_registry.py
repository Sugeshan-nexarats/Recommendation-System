from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from app.models.posts import Post
from app.retrievers.user_context import UserContext

if TYPE_CHECKING:
    from app.features.abstract_feature import AbstractFeature, FeatureResult
    from app.signals.signal_context import SignalContext

logger = logging.getLogger(__name__)


class FeatureRegistry:


    
    _registry: dict[str, "AbstractFeature"] = {}

  
    @classmethod
    def register(cls, feature_cls: type["AbstractFeature"]) -> type["AbstractFeature"]:
      
        instance: "AbstractFeature" = feature_cls()
        name = instance.name

        if name in cls._registry:
            raise ValueError(
                f"FeatureRegistry: duplicate feature name '{name}'. "
                f"Existing: {type(cls._registry[name]).__name__}, "
                f"Conflicting: {feature_cls.__name__}."
            )

        cls._registry[name] = instance
        logger.debug("FeatureRegistry: registered feature '%s'", name)
        return feature_cls

    @classmethod
    def all_features(cls) -> list["AbstractFeature"]:
        """Return all registered feature instances in registration order."""
        return list(cls._registry.values())

    @classmethod
    def feature_names(cls) -> list[str]:
        """Return the canonical names of all registered features."""
        return list(cls._registry.keys())

    @classmethod
    def compute_all(
        cls,
        user: UserContext,
        post: Post,
        signal_context: "SignalContext | None" = None,
    ) -> list["FeatureResult"]:
      
       
        from app.features.abstract_feature import FeatureResult  # noqa: PLC0415

        results: list[FeatureResult] = []

        for feature in cls._registry.values():
            try:
                logger.debug(
                    "FeatureRegistry: computing '%s' for post_id=%s content_type=%r",
                    feature.name,
                    getattr(post, "post_id", "?"),
                    signal_context.content_type if signal_context else None,
                )
                result = feature.compute(user, post, signal_context)
                results.append(result)
            except Exception:  # noqa: BLE001
                logger.exception(
                    "FeatureRegistry: feature '%s' raised an unexpected "
                    "exception for post_id=%s. Emitting zero score.",
                    feature.name,
                    getattr(post, "post_id", "unknown"),
                )
                results.append(
                    FeatureResult(
                        feature_name=feature.name,
                        score=0.0,
                        metadata={"error": "computation_failed"},
                    )
                )

        return results

    @classmethod
    def _reset(cls) -> None:
        
        cls._registry.clear()
