"""
Quality signal auto-discovery.

Importing this module triggers @QualitySignalRegistry.register for
all concrete signal classes below.
"""

from app.features.quality.signals import content_quality_signal       # noqa: F401
from app.features.quality.signals import duplicate_signal             # noqa: F401
from app.features.quality.signals import reports_signal               # noqa: F401
from app.features.quality.signals import reputation_signal            # noqa: F401
from app.features.quality.signals import spam_signal                  # noqa: F401
