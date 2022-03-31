from cachetools import Cache, TTLCache

# A TTL cache, only used for the (large) '/collections' endpoint
# TTL set to 600 seconds == 10 minutes
collections_endpoint_cache: Cache = TTLCache(maxsize=1, ttl=600)

# A TTL cache, only used for computed all-collection queryables
# TTL set to 21600 seconds == 6 hours
queryables_endpoint_cache: Cache = TTLCache(maxsize=1, ttl=21600)
