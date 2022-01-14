import unittest

from pccommon.tracing import _parse_cqljson
from .data.cql import cql, cql2, cql2_nested, cql2_no_collection, cql_multi


class TestSearchTracing(unittest.TestCase):
    def test_tracing(self) -> None:
        pass

    def test_cql_collection_parsing(self) -> None:
        collection_id, item_id = _parse_cqljson(cql)

        self.assertEqual(collection_id, "landsat")
        self.assertEqual(item_id, "l8_12345")

    def test_cql_multi_collection_parsing(self) -> None:
        collection_id, item_id = _parse_cqljson(cql_multi)

        self.assertEqual(collection_id, "landsat,sentinel")
        self.assertEqual(item_id, None)

    def test_cql2_collection_parsing(self) -> None:
        collection_id, item_id = _parse_cqljson(cql2)

        self.assertEqual(collection_id, "landsat")
        self.assertEqual(item_id, None)

    def test_cql2_nested_multi_collection_parsing(self) -> None:
        collection_id, item_id = _parse_cqljson(cql2_nested)

        self.assertEqual(collection_id, "landsat,sentinel")
        self.assertEqual(item_id, "l8_12345,s2_12345")

    def test_cql2_no_collection(self) -> None:
        collection_id, item_id = _parse_cqljson(cql2_no_collection)

        self.assertEqual(collection_id, None)
        self.assertEqual(item_id, None)
