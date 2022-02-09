from urllib.parse import quote_plus

from pccommon.config import get_render_config
from pccommon.collections import DefaultRenderConfig

multi_assets = DefaultRenderConfig(
    assets=["data1", "data2"],
    render_params={"colormap_name": "terrain", "rescale": [-1000, 4000]},
    minzoom=8,
)

single_asset = DefaultRenderConfig(
    assets=["data1"],
    render_params={"colormap_name": "terrain", "rescale": [-1000, 4000]},
    minzoom=8,
)

no_assets = DefaultRenderConfig(
    render_params={
        "expression": ("asset1," "0.45*asset2," "asset3/asset1"),
        "colormap_name": "terrain",
        "rescale": [-1000, 4000],
    },
    minzoom=8,
)


def test_multi_asset() -> None:
    qs = multi_assets.get_full_render_qs("my_collection_id", "my_item_id")
    assert qs == (
        "collection=my_collection_id&item=my_item_id&"
        "assets=data1&assets=data2&colormap_name=terrain&rescale=-1000,4000"
    )


def test_single_asset() -> None:
    qs = single_asset.get_full_render_qs("my_collection_id", "my_item_id")
    assert qs == (
        "collection=my_collection_id&item=my_item_id&assets=data1&"
        "colormap_name=terrain&rescale=-1000,4000"
    )


def test_no_asset() -> None:
    qs = no_assets.get_full_render_qs("my_collection_id", "my_item_id")
    encoded_params = quote_plus("asset1,0.45*asset2,asset3/asset1")
    assert qs == (
        f"collection=my_collection_id&item=my_item_id&expression={encoded_params}"
        "&colormap_name=terrain&rescale=-1000,4000"
    )


def test_collection_only() -> None:
    qs = single_asset.get_full_render_qs("my_collection_id")
    assert qs == (
        "collection=my_collection_id&assets=data1&colormap_name=terrain&"
        "rescale=-1000,4000"
    )
