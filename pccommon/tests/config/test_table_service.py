import pytest

from pccommon.tables import TableService


def test_table_service_azurite() -> None:
    with TableService.from_environment(
        account_name="devstoreaccount1",
        table_name="testtable",
        account_url="http://azurite:10002",
    ) as table:
        assert table
        assert table.table_name == "testtable"
        assert table.account_name == "devstoreaccount1"


def test_table_service_fails_without_azurite() -> None:
    with pytest.raises(ValueError) as excinfo:
        with TableService.from_environment(
            account_name="devstoreaccount1",
            table_name="testtable",
            account_url="https://devstoreaccount1.table.core.windows.net",
        ) as _:
            pass

    assert str(excinfo.value) == (
        "Non-azurite account url provided. "
        "Account keys can only be used with Azurite emulator."
    )
