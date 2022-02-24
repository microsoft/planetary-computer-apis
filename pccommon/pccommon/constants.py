DEFAULT_COLLECTION_CONFIG_TABLE_NAME = "collectionconfig"
DEFAULT_CONTAINER_CONFIG_TABLE_NAME = "containerconfig"

DEFAULT_TTL = 600  # 10 minutes

RATE_LIMIT_KEY_PREFIX = "rate:"
BACKPRESSURE_KEY_PREFIX = "backp:"

# Headers containing information about the requester's
# IP address. Checked in the order listed here.
X_AZURE_CLIENTIP = "X-Azure-ClientIP"
X_ORIGINAL_FORWARDED_FOR = "X-Original-Forwarded-For"
X_FORWARDED_FOR = "X-Forwarded-For"

HTTP_429_TOO_MANY_REQUESTS = 429
