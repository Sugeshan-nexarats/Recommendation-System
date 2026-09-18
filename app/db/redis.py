import os
from redis import Redis

REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_MAX_CONNECTIONS: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))

_redis_client: Redis | None = None

def get_redis_client() -> Redis:
    """Provide a globally reused Redis client instance."""
    global _redis_client
    if _redis_client is None:

        _redis_client = Redis.from_url(
            REDIS_URL, 
            decode_responses=True,
            socket_timeout=0.5,
            socket_connect_timeout=0.5,
            max_connections=REDIS_MAX_CONNECTIONS
        )
    return _redis_client
