from cachetools import TTLCache

# A TTL cache, only used for the (large) '/collections' endpoint
# TTL set to 600 seconds == 10 minutes
collections_endpoint_cache: TTLCache = TTLCache(maxsize=1, ttl=600)
