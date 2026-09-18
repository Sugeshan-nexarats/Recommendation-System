from app.features.people.abstract_people_feature import AbstractPeopleFeature, FeatureResult
from app.retrievers.user_context import UserContext
from app.features.interest.user_interest_profile import UserInterestProfile

class InterestSimilarityFeature(AbstractPeopleFeature):

    @property
    def name(self) -> str:
        return "interest_similarity"

    def compute(
        self,
        viewer: UserContext,
        candidate: UserContext
    ) -> FeatureResult:
        viewer_profile = UserInterestProfile.from_user_context(viewer)
        candidate_profile = UserInterestProfile.from_user_context(candidate)

        viewer_weights = dict(viewer_profile.tag_weights)
        for pref in viewer.user_preferences:
            name = pref.preference_name.strip().lower()
            viewer_weights[name] = viewer_weights.get(name, 0.0) + pref.preference_weight

        candidate_weights = dict(candidate_profile.tag_weights)
        for pref in candidate.user_preferences:
            name = pref.preference_name.strip().lower()
            candidate_weights[name] = candidate_weights.get(name, 0.0) + pref.preference_weight

        if not viewer_weights or not candidate_weights:
            return FeatureResult(
                feature_name=self.name,
                score=0.0,
                metadata={"reason": "One or both profiles lack interest signals"}
            )

        viewer_tags = set(viewer_weights.keys())
        candidate_tags = set(candidate_weights.keys())
        all_tags = viewer_tags | candidate_tags

        weighted_intersection = 0.0
        weighted_union = 0.0
        shared_interests = []

        for tag in all_tags:
            w_viewer = viewer_weights.get(tag, 0.0)
            w_candidate = candidate_weights.get(tag, 0.0)

            min_w = min(w_viewer, w_candidate)
            max_w = max(w_viewer, w_candidate)

            weighted_intersection += min_w
            weighted_union += max_w

           
            if min_w > 0:
                shared_interests.append((tag, min_w))

        if weighted_union == 0.0:
            score = 0.0
        else:
            score = weighted_intersection / weighted_union
            
      
        shared_interests.sort(key=lambda x: x[1], reverse=True)
        top_shared = [tag.title() for tag, _ in shared_interests[:3]]

        metadata = {
            "weighted_intersection": weighted_intersection,
            "weighted_union": weighted_union,
            "shared_tags": top_shared
        }

        
        if top_shared:
            metadata["reason_string"] = f"Shared interests in {', '.join(top_shared)}"

        return FeatureResult(
            feature_name=self.name,
            score=min(max(score, 0.0), 1.0),
            metadata=metadata
        )
