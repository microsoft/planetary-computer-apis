import pytest

from pccommon.config.core import TableConfig


def test_raises_on_non_azurite_account_url() -> None:

    invalid_url = "https://example.com"
    with pytest.raises(ValueError) as exc_info:
        TableConfig(account_url=invalid_url, table_name="test", account_name="test")

    assert (
        "Non-azurite account url provided. "
        "Account keys can only be used with Azurite emulator."
    ) in str(exc_info.value)


def test_settings_accepts_azurite_url() -> None:
    valid_url = "http://azurite:12345"

    config = TableConfig(account_url=valid_url, table_name="test", account_name="test")
    assert config.account_url == valid_url
