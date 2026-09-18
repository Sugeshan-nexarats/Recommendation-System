
INTERACTION_SOURCE_WEIGHTS: dict[str, float] = {
    "explicit":    1.00,  # interest_tags: declared preferences
    "saved":       0.90,  # saved_tags: intent to revisit
    "liked":       0.80,  # liked_tags: positive endorsement
    "interacted":  0.60,  # interacted_tags: active engagement
    "watched":     0.50,  # watched_tags: passive consumption
}

def get_weight_for_interaction_type(interaction_type: str) -> float:
    """
    Map a raw database interaction_type to its corresponding source weight.
    """
    if interaction_type == "like":
        return INTERACTION_SOURCE_WEIGHTS["liked"]
    elif interaction_type == "save":
        return INTERACTION_SOURCE_WEIGHTS["saved"]
    elif interaction_type == "watch":
        return INTERACTION_SOURCE_WEIGHTS["watched"]
    elif interaction_type in ("comment", "share"):
        return INTERACTION_SOURCE_WEIGHTS["interacted"]
    return 0.0
