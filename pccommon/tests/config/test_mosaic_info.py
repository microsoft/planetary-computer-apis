from pccommon.config.collections import MosaicInfo


def test_parse() -> None:
    d = {
        "mosaics": [
            {
                "name": "Most recent",
                "description": "",
                "cql": [
                    {
                        "op": "<=",
                        "args": [{"property": "datetime"}, {"timestamp": "2020-05-06"}],
                    }
                ],
            }
        ],
        "renderOptions": [
            {
                "name": "Elevation (terrain)",
                "description": "Elevation...",
                "options": "assets=data&rescale=-1000,4000&colormap_name=terrain",
                "minZoom": 8,
                "conditions": [{"property": "mode", "value": "Q"}],
            },
            {
                "name": "Elevation (viridis)",
                "description": "Elevation...",
                "options": "assets=data&rescale=-1000,4000&colormap_name=viridis",
                "minZoom": 8,
            },
            {
                "name": "Elevation (gray)",
                "description": "Elevation data scaled -1000 to 4000 with gray colormap",
                "options": "assets=data&rescale=-1000,4000&colormap_name=gray_r",
                "minZoom": 8,
            },
        ],
        "defaultLocation": {"zoom": 8, "coordinates": [47.1113, -120.8578]},
    }
    model = MosaicInfo.model_validate(d)
    serialized = model.model_dump(by_alias=True, exclude_unset=True)

    assert d == serialized


def test_parse_with_legend() -> None:
    d = {
        "mosaics": [
            {
                "name": "Most recent",
                "description": "",
                "cql": [
                    {
                        "op": "=",
                        "args": [{"property": "datetime"}, {"timestamp": "2020-07-01"}],
                    }
                ],
            }
        ],
        "renderOptions": [
            {
                "name": "Water occurrence",
                "description": "Shows where surface water...",
                "options": "assets=occurrence&colormap_name=jrc-occurrence&nodata=0",
                "minZoom": 4,
                "legend": {
                    "type": "continuous",
                    "labels": ["Sometimes water", "Always water"],
                    "trimStart": 1,
                },
            },
            {
                "name": "Annual water recurrence",
                "description": "Shows frequency that water...",
                "options": "assets=recurrence&colormap_name=jrc-recurrence&nodata=0",
                "minZoom": 4,
                "legend": {
                    "type": "continuous",
                    "labels": [">0%", "100%"],
                    "trimStart": 1,
                    "trimEnd": 2,
                    "scaleFactor": 0.01,
                },
            },
            {
                "name": "Water Occurrence change intensity",
                "description": "Shows where surface water occurrence...",
                "options": "assets=change&colormap_name=jrc-change&nodata=0",
                "minZoom": 4,
                "legend": {
                    "type": "continuous",
                    "labels": ["Decrease", "No change", "Increase"],
                    "trimEnd": 3,
                },
            },
            {
                "name": "Water seasonality",
                "description": "Indicates more seasonal...",
                "options": "assets=seasonality&colormap_name=jrc-seasonality&nodata=0",
                "minZoom": 4,
                "legend": {
                    "type": "continuous",
                    "labels": ["Seasonal", "Permanent"],
                    "trimStart": 1,
                    "trimEnd": 1,
                },
            },
            {
                "name": "Water transitions",
                "description": "Classifies the change in water state...",
                "options": "assets=transitions&colormap_name=jrc-transitions&nodata=0",
                "minZoom": 4,
            },
            {
                "name": "Maximum water extent",
                "description": "Show the maximum observed water...",
                "options": "assets=extent&colormap_name=jrc-extent&nodata=0",
                "minZoom": 4,
            },
        ],
        "defaultLocation": {"zoom": 10, "coordinates": [24.21647, 91.015209]},
    }

    model = MosaicInfo.model_validate(d)
    serialized = model.model_dump(by_alias=True, exclude_unset=True)

    assert d == serialized
