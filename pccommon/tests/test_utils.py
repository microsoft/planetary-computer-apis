import pccommon.utils


def test_get_param_str() -> None:
    params = {"a": "one", "b": ["two", "1, 2"]}
    result = pccommon.utils.get_param_str(params)
    expected = "a=one&b=two&b=1%2C+2"
    assert result == expected