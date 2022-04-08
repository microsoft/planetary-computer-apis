# Collection Config

`planetary-computer-apis` contains the collection-level configuration that helps frontends (like the [Explorer]) render data and generate meaningful controls for each collection.

## Implementation

To make it easy to change render configuration without requiring a redeployment of the frontend or APIs, we store the collection configuration in Azure Storage Tables. Each deployment (testing, staging, prod) has its
own set of storage tables.

The frontend loads these tables and turns them into the Python objects defined in `pccommon/config/collections.py`. See the docstrings of those classes for details on what options are available and the meaning of each option. See the tutorial below for how to update these tables.

## Tutorial

This section walks through adding a collection configuration for a new dataset. We'll use [ALSO-PALSAR] as an example. This will add data to the Planetary Computer Test deployment, which uses the following values

* Catalog: https://planetarycomputer-test.microsoft.com/catalog
* Storage Account: `pctapisstagingsa`
* Collection config Table: `collectionconfig`

### Prerequisites

- A STAC Collection and some sample items ingested into some API (Planetary Computer Test, most likely)
- SAS API configured for your collection so that the Tiler can load the assets
- A `planetary-computer-apis` dev environment
- Read / write access to the configuration table (likely a SAS token)

### Initial config

You can view the structure of these with `pcapis dump`. We strongly recommend dumping the current collection config to disk before developing your own config. These will server as a helpful reference.

```console
$ ./scripts/console
root@8e8d9c13791e:/opt/src# export SAS="..."
root@8e8d9c13791e:/opt/src# pcapis dump -t collection --account=pctapisstagingsa --table=collectionconfig --sas=$SAS --output=collectionconfig.json
...
```

We'll make a new file for just our dataset's config, call it `alos-palsar-config.json`, and fill it in with the bare minimum required. We'll update this with good values later. The structure of this file will be detailed later, but the outer-most key should be your collection ID. When we load it in a minute, we'll perform the equivalent of a SQL upsert, using the outermost key (`alos-palsar-mosaic` in this case) as the key. We'll just add / update the record for this specific collection.

```json
{
    "alos-palsar-mosaic": {
        "render_config": {
            "render_params": {},
            "minzoom": 8,
            "requires_token": true
        },
        "queryables": {},
        "mosaic_info": {
            "mosaics": [],
            "render_options": [],
            "default_location": {
                "zoom": 8,
                "coordinates": [
                    47.1113,
                    -120.8578
                ]
            }
        }
    }
}
```

And we'll push that with

```console
root@8e8d9c13791e:/opt/src# pcapis load -t collection --account=pctapisstagingsa --table=collectionconfig --sas=$SAS --file=alos-palsar-config.json
```

At this point you should be able to visit the explorer for your deployment (e.g. https://planetarycomputer-test.microsoft.com/explore) and load that collection. If you open your browser's console you *shouldn't* see any errors about failing to load the collection configuration (though you'll likely still see errors, which we'll fix next).

### Render Parameters

The Planetary Computer uses TiTiler for dynamically rendering assets. We need to tell TiTiler how to interpret the data
it loads from Blob Storage, so it can turn the raw data into a useful image. Choosing the rendering parameters is a bit of an art and requires some trial and error.

The `/docs` endpoint documents the TiTiler REST API: https://pct-apis-staging.westeurope.cloudapp.azure.com/data/docs. Verify that the data API is able to access everything it needs by making a request to `/data/item/info` with the collection, item ID, and asset.

The easiest way to discover a good default rendering is to make requests to the `/data/item/preview` endpoint, adjusting the rendering parameters as necessary to get a good image.

You can use a tool like [Insomnia] or [Postman] to help generate the queries.

You'll most likely need to specify

* `collection`
* `item`
* `assets`

You might also want to specify `max_size`, `rescale`, and `colormap_name`.

For example, https://pct-apis-staging.westeurope.cloudapp.azure.com/data/item/preview?collection=alos-palsar-mosaic&item=N01E009_17_MOS&assets=HH

After you've found a good set of rendering options, add it to the configuration file. This goes under the `mosaic_info.render_options` key. Make sure to remove `collection`, `item`, and `max_size` from the `options`. These will be set by the frontend.

```json
{
    "alos-palsar-mosaic": {
        "render_config": {
            "render_params": {},
            "assets": [
                "HH",
                "HV",
                "date",
                "mask",
                "linci"
            ],
            "minzoom": 8,
            "requires_token": true
        },
        "queryables": {},
        "mosaic_info": {
            "mosaics": [],
            "render_options": [
                {
                    "name": "HH",
                    "description": "HH",
                    "options": "assets=HH",
                    "min_zoom": 8,
                    "legend": null
                }
            ],
            "default_location": {
                "zoom": 8,
                "coordinates": [
                    47.1113,
                    -120.8578
                ]
            }
        }
    }
}
```

Load that again (`pcapis load ...`). If you refresh the explorer, you should now see previews / thumbnails appearing in the left-hand sidebar. Make sure there are some items matching your search (you should be over an area that has some items ingested).

No items will appear on the main map yet, since we haven't configured how to mosaic items.

### Mosaic Info

To get the assets rendered on the main map, we need to tell TiTiler how to mosaic items together. A good default mosaic is "most recent", which places the most recent pixels at an area on top.

Mosaics are specified as a list of mosaic objects. Each object has a name and a CQL query. The simplest
possible configuration is the following, which relies on the default behavior of sorting by datetime (descending).

```json
{
    "alos-palsar-mosaic": {
         "mosaic_info": {
            "mosaics": [
                {
                    "name": "Most recent",
                    "description": "",
                    "cql": []
                }
            ],
         }
     }
}
```

You have a lot of flexibility here. Look at the existing examples for inspiration. Other common mosaic strategies include:

* Some form of "low cloud cover"
* Various time intervals (quarters, years for annual mosaics, ...)

### Queryables

The `queryables` object is used by the frontend to generate controls for advanced queries. The collection summaries is a good place to start when trying to figure out which queryables to add. In this example, we'll add "platform", which takes on two values:

```json
{
    "alos-palsar-mosaic": {
        "queryables": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://example.org/queryables",
            "type": "object",
            "title": "",
            "properties": {
                "datetime": {
                    "description": "Datetime",
                    "type": "string",
                    "title": "Acquired",
                    "format": "date-time",
                    "pattern": "(\\+00:00|Z)$"
                },
                "id": {
                    "title": "Item ID",
                    "description": "Item identifier",
                    "$ref": "https://schemas.stacspec.org/v1.0.0/item-spec/json-schema/item.json#/definitions/core/allOf/2/properties/id"
                },
                "platform": {
                    "title": "Platform",
                    "description": "Platform",
                    "type": "string",
                    "enum": ["ALOS", "ALOS-2"]
                }
            }
        }
    }
}
```


#### Custom Colormaps

Some assets will require custom colormaps to display properly (e.g. QA bands or landcover maps). We can use TiTiler's `colormap` parameter while developing the colormap, providing it the JSON-encoded colormap. Eventually, we'll make a Pull Request to planetary-computer-apis adding that as a proper colormap, allowing us to just use `colormap_name`.

Note that the *legend* is generated from the [`classification`](https://github.com/stac-extensions/classification) extension. 

In this case, we'll define the colormap mapping from integers to hex colors. Substitute your assets, collection, item ID, and colormap.

```python
import json
from IPython.display import Image
import urllib

cmap = {
    "0": "#000000",
    "50": "#0000FF",
    "100": "#AAAA00",
    "150": "#005555",
    "255": "#AA9988",
}
cmap2 = urllib.parse.urlencode({"colormap": json.dumps(cmap)})
url = f"https://pct-apis-staging.westeurope.cloudapp.azure.com/data/item/preview.png?assets=mask&max_size=1000&collection=alos-palsar-mosaic&item=N00E008_15_MOS&{cmap2}&colormap_type=linear"
print(url)
Image(url=url)
```

See https://developmentseed.org/titiler/examples/code/tiler_with_custom_colormap/ for more. Once you're satisfied with the colormap, add it to `pctiler/colormaps/<dataset.py>` and import / register it in `pctiler/colormaps/__init__.py`. Then update your collection config to use that colormap name.

```json
{
    "alos-palsar-mosaic": {
        "mosaic_info": {
            "render_options": [
                {
                    "name": "mask",
                    "description": "Quality mask",
                    "options": "assets=mask&colormap_name=alos_palsar_mosaic",
                    "min_zoom": 8,
                    "legend": {
                        "type": "classmap",
                        "labels": [
                            "No data",
                            "Ocean and water",
                            "Radar layover",
                            "Radar shadowing",
                            "Land"
                        ]
                    }
                }
            ]
        }
    }
}
```

#### Choosing Zoom Levels

One of the options we just configured was the `min_zoom`, which controls how far out users can zoom. We typically set a minimum zoom to prevent users from accidentally requesting too many STAC items / assets.

The main things to consider when choosing a minimum zoom are:

1. How large (in latitude / longitude) are in your STAC items? If the STAC items are relatively large, meaning you have fewer items matching a query for a given AOI, then you can choose a relatively large `min_zoom`. If the STAC items are relatively small, then you should choose a relatively small `min_zoom`.
2. How large are the assets (using overviews where relevant)? We want to avoid swamping the user's browser with too much data (in bytes) if they zoom out too far. If the assets being visualized are relatively large (e.g. NAIP), then choose a smaller `min_zoom`. If the assets are relatively small (e.g. IO LULC), choose a larger `min_zoom`).

Keep in mind the data type of the data (after an expressions have been applied). float32 / float64 assets will be more expensive to transmit and render than uint8!kk

#### Setting a default query

The Data Catalog includes an "Explore" link. Following that link will take you to the default location for this collection. Choose a query that's visually interesting.

```json
{
    "alos-palsar-mosaic": {
        "mosaic_info": {
            "default_location": {
                "zoom": 8,
                "coordinates": [
                    10.6485,
                    0.0385
                ]
            }
        }
    }
}
```

[ALOS-PALSAR]: https://planetarycomputer.microsoft.com/dataset/alos-palsar-mosaic
[Explorer]: https://planetarycomputer.microsoft.com/explore
[Insomnia]: https://insomnia.rest/
[Postman]: https://www.postman.com/product/rest-client/