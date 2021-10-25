# How to generate SAS token/sign requests

The Planetary Computer service supports several use cases for interacting with
data, one of which is interacting directly with the underlying imagery. All
metadata in the Planetary Computer is publicly available. Shared access
signature tokens (SAS tokens) enable you to access the underlying data. All
underlying imagery is stored on Azure Blob Storage, and may only be accessed
directly via the use of shared access signatures (SAS tokens).

In this how-to article, you will learn how to request SAS tokens and supply them
on requests for imagery blobs.

## When a SAS token is needed

A SAS token is needed whenever an Azure Blob URL is returned in a request and
you desire to download the data. For example, in [How to read a STAC Item in the
Planetary Computer STAC catalog](./01-how-to-read-a-stac-item.md), the assets
retrieved are Azure Blob URLs. A SAS token will need to be appended to the blob
URL as query parameters.

For example, an Azure Blob URL may look like:
`https://naipeuwest.blob.core.windows.net/naip/01.tif`. And an example SAS token
may look like:
`se=2021-04-08T18%3A49%3A29Z&sp=rl&sip=20.73.55.19&sv=2020-02-10&sr=c&skoid=cccccccc-dddd-4444-aaaa-eeeeeeeeeeee&sktid=***&skt=2021-04-08T17%3A47%3A29Z&ske=2021-04-09T17%3A49%3A29Z&sks=b&skv=2020-02-10&sig=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb%3D`.

Combining the URL with the SAS token, remembering to place a `?` in between will
result in:
`https://naipeuwest.blob.core.windows.net/naip/01.tif?se=2021-04-08T18%3A49%3A29Z&sp=rl&sip=20.70.50.10&sv=2020-02-10&sr=c&skoid=cccccccc-dddd-4444-aaaa-eeeeeeeeeeee&sktid=***&skt=2021-04-08T17%3A47%3A29Z&ske=2021-04-09T17%3A49%3A29Z&sks=b&skv=2020-02-10&sig=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb%3D`.
The resulting URL may then be downloaded.

## Endpoints for requesting a SAS token

There are two endpoints that may be used to obtain a SAS token:
  1) the token endpoint: `https://planetarycomputer.microsoft.com/data/v1/token/{DATASET}`
  2) the sign endpoint: `https://planetarycomputer.microsoft.com/data/v1/sign`

The `token` endpoint allows for the generation of a SAS token for a given
dataset, which can then be used for all requests for that same dataset. Here,
datasets correspond to [STAC collections](https://github.com/radiantearth/stac-spec/blob/v1.0.0/collection-spec/collection-spec.md). For
example, to obtain a SAS token for the `naip` dataset, a request may be made to:
`https://planetarycomputer.microsoft.com/data/v1/token/naip`. An example
response may look like:

```json
{
    "msft:expiry":"2021-04-08T18:49:29Z",
    "token":"se=2021-04-08T18%3A49%3A29Z&sp=rl&sip=20.73.55.19&sv=2020-02-10&sr=c&skoid=cccccccc-dddd-4444-aaaa-eeeeeeeeeeee&sktid=***&skt=2021-04-08T17%3A47%3A29Z&ske=2021-04-09T17%3A49%3A29Z&sks=b&skv=2020-02-10&sig=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb%3D"
}
```

The `token` field is the SAS token.  The `msft:expiry` field specifies (in UTC)
when this token expires. For reference documentation on expiration times and how
to increase them, see: [Rate limits and access
restrictions](./reference-rate-limits-and-access-restrictions.md).

The `sign` endpoint makes it easy to convert an unsigned blob URL to a signed
URL by passing the URL directly into the endpoint with the `href` parameter. For
example:
`https://planetarycomputer.microsoft.com/data/v1/sign?href=https://naipeuwest.blob.core.windows.net/naip/01.tif`
returns JSON such as:

```json
{
    "msft:expiry":"2021-04-08T18:49:29Z",
    "href":"https://naipeuwest.blob.core.windows.net/naip/01.tif?se=2021-04-08T18%3A49%3A29Z&sp=rl&sip=20.73.55.19&sv=2020-02-10&sr=c&skoid=cccccccc-dddd-4444-aaaa-eeeeeeeeeeee&sktid=***&skt=2021-04-08T17%3A47%3A29Z&ske=2021-04-09T17%3A49%3A29Z&sks=b&skv=2020-02-10&sig=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb%3D"
}
```

The `href` field here contains the full, signed URL which may be used directly.


## Supplying an API subscription key

An API subscription key may be supplied to increase [rate
limits](./reference-rate-limits-and-access-restrictions.md) in one of two ways:

Supply it in an `Ocp-Apim-Subscription-Key` on request header, example:
```bash
curl -H "Ocp-Apim-Subscription-Key: 123456789" https://planetarycomputer.microsoft.com/data/v1/token/naip?subscription-key=123456789
```
Supply it in a `subscription-key` query parameter, example:
```bash
curl https://planetarycomputer.microsoft.com/data/v1/token/naip?subscription-key=123456789
```


## Planetary Computer SDK for Python

The [Planetary Computer SDK for
Python](https://github.com/microsoft/planetary-computer-sdk-for-python) makes
the above process more straightforward by providing a library that calls these
endpoints to sign URLs, and even sign all assets within a
[PySTAC](https://github.com/stac-utils/pystac) item. A cache is also kept, which
tracks expiration values, to ensure new SAS tokens are only requested when
needed.

Here's an example of using the library to sign a single URL:

```python
import planetary_computer as pc
import pystac

item: pystac.Item = ...  # Landsat item

b4_href = pc.sign(item.assets['SR_B4'].href)

with rasterio.open(b4_href) as ds:
   ...
```

And here's an example of using the library to sign all assets in a
[PySTAC](https://github.com/stac-utils/pystac) item:

```python
import pystac
import planetary_computer as pc

raw_item: pystac.Item = ...
item: pystac.Item = pc.sign_assets(raw_item)

# Now use the item however you want. All appropriate assets are signed for read access.
```

This library may be installed via:

```bash
pip install planetarycomputer
```

Once installed, the CLI may be used to supply an API subscription key to
increase [rate limits](./reference-rate-limits-and-access-restrictions.md)

```bash
planetarycomputer configure
```
