from urllib.parse import quote_plus

from pccommon.config import get_render_config
from pccommon.config.collections import DefaultRenderConfig

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
        "assets=data1&assets=data2&colormap_name=terrain&rescale=-1000&rescale=4000"
    )


def test_single_asset() -> None:
    qs = single_asset.get_full_render_qs("my_collection_id", "my_item_id")
    assert qs == (
        "collection=my_collection_id&item=my_item_id&assets=data1&"
        "colormap_name=terrain&rescale=-1000&rescale=4000"
    )


def test_no_asset() -> None:
    qs = no_assets.get_full_render_qs("my_collection_id", "my_item_id")
    encoded_params = quote_plus("asset1,0.45*asset2,asset3/asset1")
    assert qs == (
        f"collection=my_collection_id&item=my_item_id&expression={encoded_params}"
        "&colormap_name=terrain&rescale=-1000&rescale=4000"
    )


def test_collection_only() -> None:
    qs = single_asset.get_full_render_qs("my_collection_id")
    assert qs == (
        "collection=my_collection_id&assets=data1&colormap_name=terrain&"
        "rescale=-1000&rescale=4000"
    )


def test_get_render_config() -> None:
    config = get_render_config("naip")
    assert config
    encoded_params = quote_plus("image|1,2,3")
    assert (
        config.get_full_render_qs("naip")
        == f"collection=naip&assets=image&asset_bidx={encoded_params}"
    )


def test_listlike_rescale() -> None:
    config = DefaultRenderConfig(
        render_params={
            "expression": "HH,HV,HH/HV",
            "rescale": ["0,9000", "0,1000", "0,1"],
        },
        minzoom=12,
    )
    result = config.get_full_render_qs("test")
    assert result == (
        "collection=test&expression=HH%2CHV%2CHH%2FHV&"
        "rescale=0%2C9000&rescale=0%2C1000&rescale=0%2C1"
    )
