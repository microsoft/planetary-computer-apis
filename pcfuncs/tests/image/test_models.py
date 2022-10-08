from typing import Any, Dict

from image.models import ImageRequest


def test_request_parses_geometry() -> None:
    geom = {
        "type": "Polygon",
        "coordinates": [
            [
                [-79.09062791441062, 43.08554661560049],
                [-79.0629876337021, 43.08554661560049],
                [-79.0629876337021, 43.067969831431895],
                [-79.09062791441062, 43.067969831431895],
                [-79.09062791441062, 43.08554661560049],
            ]
        ],
    }
    req1: Dict[str, Any] = {
        "geometry": geom,
        "cql": {
            "filter-lang": "cql2-json",
            "filter": {
                "op": "and",
                "args": [{"op": "=", "args": [{"property": "collection"}, "naip"]}],
            },
        },
        "render_params": "assets=image&asset_bidx=image|1,2,3&collection=naip",
        "cols": 1080,
        "rows": 1080,
        "showBranding": True,
    }
    assert ImageRequest(**req1).get_geometry() == geom

    req2: Dict[str, Any] = {
        "geometry": geom,
        "cql": {
            "filter-lang": "cql2-json",
            "filter": {
                "op": "and",
                "args": [
                    {"op": "s_intersects", "args": [{"property": "geometry"}, geom]},
                    {"op": "=", "args": [{"property": "collection"}, "naip"]},
                ],
            },
        },
        "render_params": "assets=image&asset_bidx=image|1,2,3&collection=naip",
        "cols": 1080,
        "rows": 1080,
        "showBranding": True,
    }

    assert ImageRequest(**req2).get_geometry() == geom
