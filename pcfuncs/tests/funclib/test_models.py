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
