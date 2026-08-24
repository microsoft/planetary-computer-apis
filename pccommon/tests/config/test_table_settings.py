import pytest

from pccommon.config.core import PCAPIsConfig, TableConfig


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


def test_settings_table_clients_are_cached() -> None:
    config = PCAPIsConfig(
        collection_config=TableConfig(account_name="test", table_name="collection"),
        container_config=TableConfig(account_name="test", table_name="container"),
        ip_exception_config=TableConfig(account_name="test", table_name="ip_exception"),
        redis_hostname="localhost",
        redis_password="test",
        redis_port=6379,
    )

    assert config.get_collection_config_table() is config.get_collection_config_table()
    assert config.get_container_config_table() is config.get_container_config_table()
    assert config.get_ip_exception_list_table() is config.get_ip_exception_list_table()
