"""
features package — auto-discovery of all recommendation feature plugins.

Importing this package is the ONLY action required to register all features
with FeatureRegistry.  The import chain is:

    1. app/features/__init__.py  (this file)
    2.   → imports each concrete feature module
    3.   → each module's @FeatureRegistry.register decorator fires
    4.   → feature instance is stored in FeatureRegistry._registry

FeedEngine depends on FeatureRegistry, which is populated by the time
the application starts (FastAPI imports the route, which imports the engine,
which imports this package).

To add a new feature:
    a. Create app/features/my_feature.py with @FeatureRegistry.register.
    b. Add: from app.features import my_feature  (one line, below).
    No other changes are needed anywhere in the codebase.
"""

# Importing concrete feature modules triggers @FeatureRegistry.register
# for each class.  Order determines registration order, which affects
# the order of FeatureResult lists returned by FeatureRegistry.compute_all().

from app.features import (  # noqa: F401  (imported for side effects)
    freshness_feature,
    interest_feature,
    popularity_feature,
    preference_feature,
    quality_feature,
    relationship_feature,
    community_feature,
)
