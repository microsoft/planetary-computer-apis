from funclib.models import RenderOptions


def test_render_options_encoded_parameters() -> None:
    render_params = (
        "assets=B04&assets=B03&assets=B02&nodata=0&"
        "color_formula=Gamma RGB 3.2 Saturation 0.8 Sigmoidal RGB 25 0.35&"
        "collection=sentinel-2-l2a"
    )
    render_options = RenderOptions.from_query_params(render_params)

    assert render_options.assets == ["B04", "B03", "B02"]

    encoded_params = render_options.encoded_query_string

    assert encoded_params.count("assets=") == 3


def test_naip_render_params() -> None:
    render_params = "assets=image&asset_bidx=image|1,2,3&collection=naip"
    render_options = RenderOptions.from_query_params(render_params)
    _ = render_options.encoded_query_string

    assert render_options.assets == "image"


def test_landsat_ndvi_params() -> None:
    render_params = (
        "nodata=0&expression=(nir08-red)/(nir08+red)&rescale=-1,1&"
        "colormap_name=rdylgn&collection=landsat-c2-l2"
    )
    render_options = RenderOptions.from_query_params(render_params)
    _ = render_options.encoded_query_string

    assert render_options.rescale == "-1,1"


def test_modis_fire_params() -> None:
    render_params = (
        "assets=LST_Day_1KM&colormap_name=jet&rescale=255,310&"
        "unscale=True&collection=modis-21A2-061"
    )
    render_options = RenderOptions.from_query_params(render_params)
    _ = render_options.encoded_query_string

    assert render_options.colormap_name == "jet"
