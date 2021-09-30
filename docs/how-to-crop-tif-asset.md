# How to crop and scale a TIF asset from the Planetary Computer

Tiling assets are cropped according to a predefined pyramid with fewer tiles and lower resolution at the top of the pyramid and more, higher resolution tiles on the bottom.
Sometimes, greater control of image boundaries is required.
In this how-to you will construct an API call to crop and scale a tif asset according to two flavors of user specification: bounding box `GET` request and polygon `POST`.


### Prerequisites

- [How-to generate SAS token/sign requests](./how-to-generate-sas-token-sign-requests.md)
- (optional) Get an account (TODO)
- [How to read a STAC Item in the Planetary Computer STAC catalog](./how-to-preview-stac-entry.md)

### Cropping an asset by bounding box

Because we're cropping a single asset rather than a (potentially global) mosaic of assets, it is not unlikely that the spatial extent represented by the imagery is limited to a small region of the globe.
The first thing we should do to guarantee good results is verify the external, spatial bounds of the asset in question.
The URL we'll be constructing requires a minimum x, minimum y, maximum x, and maximum y - sometimes referred to as a bounding box.
Referring to the spatial bounding box reported on the [info endpoint](PQE_METADATA_URL/collections/naip?item=md_m_3807619_se_18_060_20181025_20190211) where the collection = 'naip' and the item = md_m_3807619_se_18_060_20181025_20190211, we see that the minimum x is -76.6919..., the minimum y is 38.6213..., the maximum x is -76.6200..., and the maximum y is 38.6916...:

```json
{
   "spatial":{
      "bbox":[
         [
            -76.69198556156623,
            38.621369461223104,
            -76.6200684427915,
            38.69162323586947
         ]
      ]
   }
}
```

> Note: the STAC item for this entry lists a `proj:bbox` field, but this is *not* what we are using to establish a tif's bounds and to construct the bounding box used in cropping.
> The difficulty with this field is that it is the bounding box as defined in the native projection of the tif whereas `crop` endpoints anticipate a bounding box defined in terms of latitude/longitude coordinates.
> The info endpoint (PQE_DATA_URL/collections/{collection_id}/map/tiles?item={item_id}), on the other hand, will *always* provide an image's extent in terms of latitude/longitude and is thus well suited for the construction of crop boundaries.

Looking to the [API reference](DQE_API_REFERENCE_URL) under the `OGC Tiles` heading, you should see that the "Bbox crop" endpoint uses template PQE_DATA_URL/collections/{collection_id}/crop/{minx},{miny},{maxx},{maxy}.{format}?item={item_id}&assets=image.
In constructing the {minx},{miny},{maxx},{maxy} portion of the crop template it is generally desirable, though not strictly necessary, to keep the minx/miny values *higher* than the minimum x/y values and the maxx/maxy values *lower* than the maximum x,y values advertised on the tif's lat/lng bbox above.
Following this rule ensures that the output imagery is fully within the region actually represented by a tif.
Any crop-region in excess of the tif's advertised coverage will be treated as `NoData` and appear as a black or transparent region in crop endpoint results.

A suitable bbox subselection with data throughout the output imagery might be minx=-76.68, miny=38.63, maxx=-76.63, maxy=38.68.
Filling out the rest of the "Bbox crop" template with the same item used in prior examples, we get PQE_DATA_URL/collections/naip/crop/-76.68,38.63,-76.63,38.68.{format}?item=md_m_3807619_se_18_060_20181025_20190211&assets=image.
For output format, we'll use `tif` so that spatial information is bundled up with the output imagery.
This format selection is ideal for analysis in desktop GIS software and will enable quick verification of output correctness.
Available formats are the same as listed above - feel free to try out some of the alternatives such as `png` or `npy`
The URL, after all templating has been attended to, should be: PQE_DATA_URL/collections/naip/crop/-76.68,38.63,-76.63,38.68.tif?item=md_m_3807619_se_18_060_20181025_20190211&assets=image


### Cropping an asset by polygon

Cropping by polygon is just like cropping by bounding box except that, instead of providing a bounding box in the API path, a polygon is supplied in a `POST` body.
Sticking to the familiar template above, all that we need to do to use the equivalent polygon crop endpoint is delete the "{minx},{miny},{maxx},{maxy}" portion of the URL, convert the `GET` to a `POST` and insert the following JSON into the `POST`'s body:

```json
{
   "type":"Polygon",
   "coordinates":[
      [
         [
            -76.68,
            38.63
         ],
         [
            -76.63,
            38.63
         ],
         [
            -76.63,
            38.68
         ],
         [
            -76.68,
            38.68
         ],
         [
            -76.68,
            38.63
         ]
      ]
   ]
}
```
