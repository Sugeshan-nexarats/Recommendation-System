"""
Relationship signal auto-discovery.

Importing this module triggers @RelationshipSignalRegistry.register for
all concrete signal classes below.

To add a new relationship signal type:
    1. Create signals/my_signal.py implementing AbstractRelationshipSignal.
    2. Add one import line below.
    RelationshipFeature, the registry, and all other signals — untouched.
"""

from app.features.relationship.signals import community_signal          # noqa: F401
from app.features.relationship.signals import creator_relationship_signal  # noqa: F401
from app.features.relationship.signals import following_signal          # noqa: F401
from app.features.relationship.signals import friendship_signal         # noqa: F401
from app.features.relationship.signals import mutual_friends_signal     # noqa: F401
from app.features.relationship.signals import past_interaction_signal   # noqa: F401
