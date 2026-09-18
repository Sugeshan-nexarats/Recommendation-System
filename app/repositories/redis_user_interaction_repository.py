import logging
from redis import Redis
from app.models.interaction_weights import get_weight_for_interaction_type

logger = logging.getLogger(__name__)

class RedisUserInteractionRepository:


    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    def update_derived_state(
        self, 
        user_id: int, 
        post_id: int, 
        interaction_type: str, 
        tags: list[str], 
        communities: list[str]
    ) -> None:
       
        try:

            if interaction_type in ("like", "save"):
                posts_key = f"user:{user_id}:interactions:posts:{interaction_type}"
                # SADD returns 1 if added, 0 if it already existed
                added = self._redis.sadd(posts_key, post_id)
                if not added:
                    logger.debug("Duplicate %s interaction for user %d on post %d ignored by Redis.", interaction_type, user_id, post_id)
                    return
            

            pipeline = self._redis.pipeline()
            
            if tags:
                # The UserContext fields are mapped by 'interact' instead of 'comment'/'share'
                tag_type = interaction_type
                if interaction_type in ("comment", "share"):
                    tag_type = "interact"
                    
                tags_key = f"user:{user_id}:interactions:tags:{tag_type}"
                
                # Each tag from the post increments the user's tag frequency count by 1
                for tag in tags:
                    normalised = str(tag).strip().lower()
                    if normalised:
                        pipeline.hincrby(tags_key, normalised, 1)
                        

            if communities:
                comm_key = f"user:{user_id}:interactions:communities"
                weight = get_weight_for_interaction_type(interaction_type)
                
                # Deduplicate communities per post before incrementing
                unique_communities = {str(c).strip() for c in communities if str(c).strip()}
                
                for comm in unique_communities:
                    pipeline.hincrbyfloat(comm_key, comm, weight)
            
            # Execute the batch
            pipeline.execute()
            
        except Exception as e:
          
            logger.exception("Failed to update Redis derived state for user %d: %s", user_id, e)

    def get_derived_state(self, user_id: int) -> dict | None:
        """
        Attempt to fetch the complete derived interaction state from Redis in a single pipeline RTT.
        Returns None if the user is uninitialized (cache miss).
        """
        pipeline = self._redis.pipeline()
        pipeline.exists(f"user:{user_id}:interactions:initialized")
        pipeline.hgetall(f"user:{user_id}:interactions:tags:like")
        pipeline.hgetall(f"user:{user_id}:interactions:tags:save")
        pipeline.hgetall(f"user:{user_id}:interactions:tags:watch")
        pipeline.hgetall(f"user:{user_id}:interactions:tags:interact")
        pipeline.hgetall(f"user:{user_id}:interactions:communities")
        
        results = pipeline.execute()
        
        initialized = results[0]
        if not initialized:
            return None
            
        return {
            "tags:like": {k.decode('utf-8'): int(v) for k, v in results[1].items()},
            "tags:save": {k.decode('utf-8'): int(v) for k, v in results[2].items()},
            "tags:watch": {k.decode('utf-8'): int(v) for k, v in results[3].items()},
            "tags:interact": {k.decode('utf-8'): int(v) for k, v in results[4].items()},
            "communities": {k.decode('utf-8'): float(v) for k, v in results[5].items()},
        }

    def backfill_state(self, user_id: int, interaction_data: dict, idempotency_sets: dict) -> None:
   
        from collections import Counter
        
        pipeline = self._redis.pipeline()
        
       
        for itype, post_ids in idempotency_sets.items():
            if post_ids:
                key = f"user:{user_id}:interactions:posts:{itype}"
                pipeline.sadd(key, *post_ids)
                
       
        tag_mappings = {
            "tags:like": Counter(interaction_data.get("liked_tags", [])),
            "tags:save": Counter(interaction_data.get("saved_tags", [])),
            "tags:watch": Counter(interaction_data.get("watched_tags", [])),
            "tags:interact": Counter(interaction_data.get("interacted_tags", []))
        }
        
        for key_suffix, counts in tag_mappings.items():
            if counts:
                key = f"user:{user_id}:interactions:{key_suffix}"
                # Using hset with mapping to overwrite any existing garbage state idempotently
                pipeline.hset(key, mapping=counts)
                
       
        communities = interaction_data.get("community_affinity", {})
        if communities:
            comm_key = f"user:{user_id}:interactions:communities"
            pipeline.hset(comm_key, mapping=communities)
            
       
        pipeline.set(f"user:{user_id}:interactions:initialized", 1)
        
        pipeline.execute()

