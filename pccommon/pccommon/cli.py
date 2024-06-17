import argparse
import json
import sys
import textwrap
from typing import Any, Dict, List, Optional

from pccommon.config.collections import CollectionConfig, CollectionConfigTable
from pccommon.config.containers import ContainerConfig, ContainerConfigTable
from pccommon.constants import (
    DEFAULT_COLLECTION_CONFIG_TABLE_NAME,
    DEFAULT_CONTAINER_CONFIG_TABLE_NAME,
    DEFAULT_IP_EXCEPTION_CONFIG_TABLE_NAME,
)
from pccommon.tables import IPExceptionListTable
from pccommon.version import __version__


def get_account_url(account: str, account_url: Optional[str]) -> str:
    return account_url or f"https://{account}.table.core.windows.net"


def load(
    sas: str, account: str, table: str, type: str, file: str, **kwargs: Any
) -> int:
    account_url = get_account_url(account, kwargs.get("account_url"))
    with open(file) as f:
        rows = json.load(f)

    if type == "collection":
        col_config_table = CollectionConfigTable.from_sas_token(
            account_url=account_url, sas_token=sas, table_name=table
        )
        for coll_id, config in rows.items():
            print("Loading config for collection", coll_id)
            try:
                col_config_table.set_config(coll_id, CollectionConfig(**config))
            except Exception as e:
                print("========================================")
                print(f"Error loading config for collection {coll_id}: {e}")
                print(f"{coll_id} has been skipped!")
                print("========================================")

    elif type == "container":
        cont_config_table = ContainerConfigTable.from_sas_token(
            account_url=account_url, sas_token=sas, table_name=table
        )
        for path, config in rows.items():
            storage_account, container = path.split("/")
            cont_config_table.set_config(
                storage_account, container, ContainerConfig(**config)
            )
    else:
        print(f"Unknown type: {type}")
        return 1

    return 0


def dump(sas: str, account: str, table: str, type: str, **kwargs: Any) -> int:
    output = kwargs.get("output")
    account_url = get_account_url(account, kwargs.get("account_url"))
    id = kwargs.get("id")
    result: Dict[str, Dict[str, Any]] = {}
    if type == "collection":
        col_config_table = CollectionConfigTable.from_sas_token(
            account_url=account_url, sas_token=sas, table_name=table
        )

        if id:
            col_config = col_config_table.get_config(id)
            assert col_config
            result[id] = col_config.model_dump()
        else:
            for _, collection_id, col_config in col_config_table.get_all():
                assert collection_id
                assert col_config
                result[collection_id] = col_config.model_dump()

    elif type == "container":
        con_config_table = ContainerConfigTable.from_sas_token(
            account_url=account_url, sas_token=sas, table_name=table
        )
        if id:
            con_account = kwargs.get("container_account")
            assert con_account
            con_config = con_config_table.get_config(con_account, id)
            assert con_config
            result[f"{con_account}/{id}"] = con_config.model_dump()
        else:
            for storage_account, container, con_config in con_config_table.get_all():
                assert con_config
                result[f"{storage_account}/{container}"] = con_config.model_dump()
    else:
        print(f"Unknown type: {type}")
        return 1

    if output:
        with open(output, "w") as f:
            json.dump(result, f, indent=2)
    else:
        print(json.dumps(result, indent=2))

    return 0


def add_ip_exception(sas: str, account: str, table: str, **kwargs: Any) -> int:
    ip_file = kwargs.get("file")
    ip = kwargs.get("ip")
    account_url = get_account_url(account, kwargs.get("account_url"))
    ip_table = IPExceptionListTable.from_sas_token(
        account_url=account_url, sas_token=sas, table_name=table
    )
    if ip:
        print(f"Adding exception for IP {ip}...")
        ip_table.add_exception(ip)
    if ip_file:
        print("Adding exceptions to the following ips...")
        with open(ip_file) as f:
            for ip_to_add in f:
                if ip_to_add:
                    ip_to_add = ip_to_add.strip()
                    print(f" {ip_to_add}")
                    ip_table.add_exception(ip_to_add)
    return 0


def parse_args(args: List[str]) -> Optional[Dict[str, Any]]:
    desc = "pcapis CLI"
    dhf = argparse.ArgumentDefaultsHelpFormatter
    parser0 = argparse.ArgumentParser(description=desc)
    parser0.add_argument(
        "--version",
        help="Print version and exit",
        action="version",
        version=__version__,
    )

    parent = argparse.ArgumentParser(add_help=False)
    subparsers = parser0.add_subparsers(dest="command")

    def add_common_opts(p: argparse.ArgumentParser, default_table: str) -> None:
        p.add_argument(
            "--sas",
            help="SAS Token for the storage account.",
            required=True,
        )
        p.add_argument("--account", help="Storage account name.", required=True)
        p.add_argument("--table", help="Table name.", default=default_table)
        p.add_argument(
            "--account-url",
            help="Storage account endpoint for table access.",
            default=None,
        )

    # collection config commands
    parser = subparsers.add_parser(
        "load",
        help="Load config into a storage table",
        parents=[parent],
        formatter_class=dhf,
    )
    parser.add_argument(
        "--file",
        help=textwrap.dedent(
            """\
            Filename to load collection configuration from.

            Keys in this file are merged with existing records. Use
            just a single item if you want to update a single record
            in the table.
        """
        ),
        required=True,
    )
    parser.add_argument(
        "-t",
        "--type",
        help="Type of configuration.",
        choices=["collection", "container"],
        required=True,
    )
    add_common_opts(parser, DEFAULT_COLLECTION_CONFIG_TABLE_NAME)

    parser = subparsers.add_parser(
        "dump",
        help="Dump config from a storage table",
        parents=[parent],
        formatter_class=dhf,
    )
    parser.add_argument(
        "--output", help="Filename to save collections to", default=None
    )

    parser.add_argument(
        "--id", help="Single collection or container id to dump", default=None
    )
    parser.add_argument(
        "--container-account",
        help="Storage account of the specified container config id (PartitionKey)",
        default=None,
    )
    parser.add_argument(
        "-t",
        "--type",
        help="Type of configuration.",
        choices=["collection", "container"],
        required=True,
    )
    add_common_opts(parser, DEFAULT_CONTAINER_CONFIG_TABLE_NAME)

    parser = subparsers.add_parser(
        "add-ip-exception",
        help="Add an exception to the ip table. This IP will not be rate limited.",
        parents=[parent],
        formatter_class=dhf,
    )
    parser.add_argument(
        "--file", help="File that lists IPs, one per line", default=None
    )
    parser.add_argument("--ip", help="IP to add as an exception", default=None)
    add_common_opts(parser, DEFAULT_IP_EXCEPTION_CONFIG_TABLE_NAME)

    parsed_args = {
        k: v for k, v in vars(parser0.parse_args(args)).items() if v is not None
    }
    if "command" not in parsed_args:
        parser0.print_usage()
        return None

    return parsed_args


def cli() -> int:
    args = parse_args(sys.argv[1:])
    if not args:
        return -1

    cmd = args.pop("command")

    if cmd == "load":
        return load(**args)
    elif cmd == "dump":
        return dump(**args)
    elif cmd == "add-ip-exception":
        return add_ip_exception(**args)

    return 2


if __name__ == "__main__":
    return_code = cli()
    if return_code and return_code != 0:
        sys.exit(return_code)
