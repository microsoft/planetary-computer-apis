# Data Query Engine MVP Endpoints

This document serves to lay out the HTTP endpoints that the Data Query Engine will support for the initial MVP.

We will support the following endpoints:

1. `/collections/<collection-id>/items/<item-id>/tiles` - tile description document that describes how to retrieve tiles, which tile matrix sets are available, how to specify band combinations, and what formats are available. We should be able to lean on [TiTiler STAC Info](https://devseed.com/titiler/endpoints/stac/#info) and [TiTiler STAC Metadata](https://devseed.com/titiler/endpoints/stac/#metadata) but may need some custom logic to show the correct url for the actual tile endpoints. 
2. `/collections/<collection-id>/items/<item-id>/tiles/{matrix-set-id}/{z}/{x}/{y}?format=<format>&<other-params>` - actual tile endpoints.
  For `<other-params>` we can start by supporting the TiTiler Query Params for their tiles endpoint: https://devseed.com/titiler/endpoints/stac/#tiles, which includes:
    - assets: Comma (',') delimited asset names. OPTIONAL*
    - expression: rio-tiler's band math expression (e.g B1/B2). OPTIONAL*
    - bidx: Comma (',') delimited band indexes. OPTIONAL
    - nodata: Overwrite internal Nodata value. OPTIONAL
    - rescale: Comma (',') delimited Min,Max bounds. OPTIONAL
    - color_formula: rio-color formula. OPTIONAL
    - color_map: rio-tiler color map name. OPTIONAL
    - resampling_method: rasterio resampling method. Default is nearest.
3. `/spec` - open API spec for the DQE
4. `/tileMatrixSets` - list of supported tile matrix sets for other calls. Perhaps optional if (1) includes tile matrix set info. Intend to only provide default tms's provided by TiTiler and its dependencies.

Endpoints 1, 2, 4 will be compliant with the OGC API - Tiles specification.

Supported output formats (same as TiTiler):

- tif: image/tiff; application=geotiff
- jp2: image/jp2
- png: image/png
- pngraw: image/png
- jpg: image/jpeg
- webp: image/webp
- npy: application/x-binary

These endpoints will retrieve the appropriate URLs from STAC Items by querying the Metadata Query Engine. The data URL will then be passed to TiTiler internally to return results: https://devseed.com/titiler/endpoints/stac/#tiles
5. `/vrt` - Build a GDAL VRT from a STAC ItemCollection. The ItemCollection might
   come from the metadata query API's `/search` endpoint.