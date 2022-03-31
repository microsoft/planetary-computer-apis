from pccommon.tracing import _parse_cqljson

from .data.cql import cql, cql2, cql2_nested, cql2_no_collection, cql_multi


def test_tracing() -> None:
    pass


def test_cql_collection_parsing() -> None:
    collection_id, item_id = _parse_cqljson(cql)

    assert collection_id == "landsat"
    assert item_id == "l8_12345"


def test_cql_multi_collection_parsing() -> None:
    collection_id, item_id = _parse_cqljson(cql_multi)

    collection_id == "landsat,sentinel"
    assert item_id is None


def test_cql2_collection_parsing() -> None:
    collection_id, item_id = _parse_cqljson(cql2)

    assert collection_id == "landsat"
    assert item_id is None


def test_cql2_nested_multi_collection_parsing() -> None:
    collection_id, item_id = _parse_cqljson(cql2_nested)

    collection_id == "landsat,sentinel"
    item_id == "l8_12345,s2_12345"


def test_cql2_no_collection() -> None:
    collection_id, item_id = _parse_cqljson(cql2_no_collection)

    collection_id is None
    item_id is None
