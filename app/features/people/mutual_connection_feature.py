from app.features.people.abstract_people_feature import AbstractPeopleFeature, FeatureResult
from app.retrievers.user_context import UserContext

MAX_EXPECTED_MUTUAL_CONNECTIONS = 10.0

class MutualConnectionFeature(AbstractPeopleFeature):

    @property
    def name(self) -> str:
        return "mutual_connections"

    def _get_friend_ids(self, context: UserContext) -> set[int]:
        """Extract accepted friend IDs from the user's relationships."""
        friend_ids = set()
        for rel in context.user_relationships:
            if rel.is_accepted_friend:
                if rel.requester_user_id == context.user_id:
                    friend_ids.add(rel.target_user_id)
                else:
                    friend_ids.add(rel.requester_user_id)
        return friend_ids

    def compute(
        self,
        viewer: UserContext,
        candidate: UserContext
    ) -> FeatureResult:
        viewer_friends = self._get_friend_ids(viewer)
        candidate_friends = self._get_friend_ids(candidate)

        mutual_friends = viewer_friends & candidate_friends
        mutual_count = len(mutual_friends)

        # Normalize score up to a maximum expected count
        score = min(mutual_count / MAX_EXPECTED_MUTUAL_CONNECTIONS, 1.0)

        metadata = {
            "mutual_count": mutual_count
        }

        if mutual_count > 0:
            plural = "s" if mutual_count > 1 else ""
            metadata["reason_string"] = f"{mutual_count} mutual connection{plural}"

        return FeatureResult(
            feature_name=self.name,
            score=score,
            metadata=metadata
        )
