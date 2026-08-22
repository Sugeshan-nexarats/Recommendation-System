"""
app.filters — hard eligibility filters applied before ranking.

Components:
    VisibilityFilter: Filters candidate posts according to the viewer's
        relationship with each creator and the creator's profile_visibility
        setting.  Posts that fail the eligibility check never reach
        ContentRouter, FeatureRegistry, or RankingEngine.
"""
