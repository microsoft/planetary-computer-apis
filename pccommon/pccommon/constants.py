from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES

DEFAULT_COLLECTION_CONFIG_TABLE_NAME = "collectionconfig"
DEFAULT_CONTAINER_CONFIG_TABLE_NAME = "containerconfig"
DEFAULT_IP_EXCEPTION_CONFIG_TABLE_NAME = "ipexceptionlist"

DEFAULT_COLLECTION_REGION = "westeurope"
DEFAULT_TTL = 600  # 10 minutes
DEFAULT_IP_EXCEPTIONS_TTL = 43200  # 12 hours

RATE_LIMIT_KEY_PREFIX = "rate:"
BACKPRESSURE_KEY_PREFIX = "backp:"

IP_EXCEPTION_PARTITION_KEY = "ipexception"

# Headers containing information about the requester's
# IP address. Checked in the order listed here.
X_AZURE_CLIENTIP = "X-Azure-ClientIP"
X_ORIGINAL_FORWARDED_FOR = "X-Original-Forwarded-For"
X_FORWARDED_FOR = "X-Forwarded-For"

X_REQUEST_ENTITY = "X-PC-Request-Entity"
X_AZURE_REF = "X-Azure-Ref"

QS_REQUEST_ENTITY = "request_entity"

HTTP_429_TOO_MANY_REQUESTS = 429

HTTP_PATH = COMMON_ATTRIBUTES["HTTP_PATH"]
HTTP_URL = COMMON_ATTRIBUTES["HTTP_URL"]
HTTP_STATUS_CODE = COMMON_ATTRIBUTES["HTTP_STATUS_CODE"]
HTTP_METHOD = COMMON_ATTRIBUTES["HTTP_METHOD"]

# This is the Azurite storage account key.
# This is not a key for a real Storage Account and is publicly accessible
# on Azurite's GitHub repo. This is used only in development.
AZURITE_ACCOUNT_KEY = (
    "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUz"
    "FT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="
)
