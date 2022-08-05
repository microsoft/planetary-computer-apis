from funclib.raster import Bbox, RasterExtent
from funclib.tiles import TileSet, get_tileset_dimensions


def test_get_covering_tiles() -> None:
    geom = {
        "type": "Polygon",
        "coordinates": [
            [
                [5.2123260498046875, 23.543215649525703],
                [5.2109527587890625, 23.511737459776796],
                [5.280303955078124, 23.511737459776796],
                [5.280303955078124, 23.586643178460292],
                [5.208892822265625, 23.582238141599596],
                [5.2123260498046875, 23.543215649525703],
            ]
        ],
    }

    bbox = Bbox.from_geom(geom)

    covering_tiles = TileSet.get_covering_tiles(bbox, 1000, 1000, tile_size=512)

    xmin = min(tile.x for tile in covering_tiles)
    xmax = max(tile.x for tile in covering_tiles)
    ymin = min(tile.y for tile in covering_tiles)
    ymax = max(tile.y for tile in covering_tiles)

    coverage_height, coverage_width = (ymax - ymin) * 512, (xmax - xmin) * 512

    assert coverage_height > 1000
    assert coverage_height <= (512 * 4)
    assert coverage_width > 1000
    assert coverage_width <= (512 * 4)

    # features = [{"type": "Feature", "geometry": geom, "properties": {}}]
    # import json
    # import mercantile
    # for tile in covering_tiles:
    #     features.append(mercantile.feature(tile))
    # with open("test.geojson", "w") as f:
    #     json.dump({"type": "FeatureCollection", "features": features}, f)


def test_northern_bbox() -> None:
    geom = {
        "type": "Polygon",
        "coordinates": [
            [
                [-101.953125, 77.59884823753002],
                [-94.130859375, 77.59884823753002],
                [-94.130859375, 78.66460771205901],
                [-101.953125, 78.66460771205901],
                [-101.953125, 77.59884823753002],
            ]
        ],
    }

    original_bbox = Bbox.from_geom(geom)

    covering_tiles = TileSet.get_covering_tiles(
        original_bbox, 1000, 1000, tile_size=512
    )

    print(covering_tiles)

    tileset_dimensions = get_tileset_dimensions(covering_tiles, 512)

    print(tileset_dimensions)

    bbox = Bbox.from_tiles(covering_tiles)

    print(bbox)

    assert bbox.width > 0
    assert bbox.height > 0

    raster_extent = RasterExtent(
        bbox=bbox,
        cols=tileset_dimensions.total_cols,
        rows=tileset_dimensions.total_rows,
    )

    print(raster_extent)

    col_min, row_min = raster_extent.map_to_grid(original_bbox.xmin, original_bbox.ymax)
    col_max, row_max = raster_extent.map_to_grid(original_bbox.xmax, original_bbox.ymin)

    print(col_min, row_min, col_max, row_max)

    assert col_min > 0
    assert col_max < tileset_dimensions.total_cols
    assert row_min > 0
    assert row_max < tileset_dimensions.total_rows

    # import mercantile, json
    # fc = {
    #     "type": "FeatureCollection",
    #     "features": [mercantile.feature(t) for t in covering_tiles]
    #     + [{"type": "Feature", "geometry": geom, "properties": {}}],
    # }
    # with open("tmp.json", "w") as f:
    #     f.write(json.dumps(fc, indent=2))
