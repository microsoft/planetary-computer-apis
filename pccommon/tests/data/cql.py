cql = {
    "and": [
        {"lte": [{"property": "eo:cloud_cover"}, "10"]},
        {"gte": [{"property": "datetime"}, "2021-04-08T04:39:23Z"]},
        {
            "or": [
                {"eq": [{"property": "collection"}, "landsat"]},
                {"lte": [{"property": "gsd"}, "10"]},
            ]
        },
        {"lte": [{"property": "id"}, "l8_12345"]},
    ]
}

cql_multi = {
    "and": [
        {"lte": [{"property": "eo:cloud_cover"}, "10"]},
        {"gte": [{"property": "datetime"}, "2021-04-08T04:39:23Z"]},
        {
            "or": [
                {"eq": [{"property": "collection"}, ["landsat", "sentinel"]]},
                {"lte": [{"property": "gsd"}, "10"]},
            ]
        },
    ]
}

cql2 = {
    "op": "or",
    "args": [
        {"op": ">=", "args": [{"property": "sentinel:data_coverage"}, 50]},
        {"op": "=", "args": [{"property": "collection"}, "landsat"]},
        {
            "op": "and",
            "args": [
                {"op": "isNull", "args": {"property": "sentinel:data_coverage"}},
                {"op": "isNull", "args": {"property": "landsat:coverage_percent"}},
            ],
        },
    ],
}

cql2_nested = {
    "op": "or",
    "args": [
        {"op": ">=", "args": [{"property": "sentinel:data_coverage"}, 50]},
        {
            "op": "and",
            "args": [
                {"op": "isNull", "args": {"property": "sentinel:data_coverage"}},
                {
                    "op": "=",
                    "args": [
                        {"property": "collection"},
                        ["landsat", "sentinel"],
                    ],
                },
                {"op": "in", "args": [{"property": "id"}, ["l8_12345", "s2_12345"]]},
            ],
        },
    ],
}

cql2_no_collection = {
    "op": "or",
    "args": [{"op": ">=", "args": [{"property": "sentinel:data_coverage"}, 50]}],
}
