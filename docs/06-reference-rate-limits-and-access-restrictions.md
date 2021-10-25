# Rate limits and access restrictions

To prevent abuse, the SAS token related endpoints
([token](https://planetarycomputer.microsoft.com/data/v1/token) and
[sign](https://planetarycomputer.microsoft.com/data/v1/sign) are rate limited by
requesting IP. There are two boolean variables that control which rate limiting
policy is applied to incoming requests:
  * Whether or not the request is originating from within the same datacenter as
    the Planetary Computer service
  * Whether or not a valid API subscription key has been supplied on the request

These two variables are used to determine the tier of rate limiting which is
applied to requests, as well as the valid length of time for issued SAS tokens.


## Within datacenter

The Planetary Computer service is running within the Azure West Europe
datacenter. The IP address of incoming requests is checked against the published
set of IP ranges for the West Europe datacenter. For example, an Azure VM
running within the West Europe datacenter would pass this check. Because the
data is kept local to the datacenter, a less stringent rate limiting policy is
applied. This check is based purely on the IP of the incoming request, and no
additional headers or query parameters need to be supplied.


## Supplied subscription key

Signing up for an API subscription key is optional, however supplying one on a
request helps the system track usage and prevent abuse, and therefore allows for
a less stringent rate limiting/token expiration policy. There are two ways to
supply a subscription key on requests:
  * Supply it in an `Ocp-Apim-Subscription-Key` on request header
  * Supply it in a `subscription-key` query parameter

Alternatively, the [Planetary Computer SDK for
Python](https://github.com/microsoft/planetary-computer-sdk-for-python) may be
used to aid in this.


## Rate limits and expirations

Rate limits and expiration values table based on the two variables defined
above:

| Variables                           | Requests per minute | Token expiration minutes |
|-------------------------------------|---------------------|--------------------------|
|Within datacenter, with subscription | 120                 | 60 * 24 * 32 (~1 month)  |
|Within datacenter, no subscription   | 60                  | 60 (1 hour)              |
|Outside datacenter, with subscription| 10                  | 60 (1 hour)              |
|Outside datacenter, no subscription  | 5                   | 5                        |
