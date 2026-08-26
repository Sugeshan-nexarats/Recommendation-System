
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
