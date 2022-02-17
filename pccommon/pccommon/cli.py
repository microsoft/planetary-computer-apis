import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from pccommon.config.collections import CollectionConfig, CollectionConfigTable
from pccommon.config.containers import ContainerConfig, ContainerConfigTable
from pccommon.constants import DEFAULT_COLLECTION_CONFIG_TABLE_NAME
from pccommon.version import __version__


def load(sas: str, account: str, table: str, type: str, file: str) -> int:
    account_url = f"https://{account}.table.core.windows.net"
    with open(file) as f:
        rows = json.load(f)

    if type == "collection":
        col_config_table = CollectionConfigTable.from_sas_token(
            account_url=account_url, sas_token=sas, table_name=table
        )
        for coll_id, config in rows.items():
            col_config_table.set_config(coll_id, CollectionConfig(**config))

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
    account_url = f"https://{account}.table.core.windows.net"
    id = kwargs.get("id")
    result: Dict[str, Dict[str, Any]] = {}
    if type == "collection":
        col_config_table = CollectionConfigTable.from_sas_token(
            account_url=account_url, sas_token=sas, table_name=table
        )

        if id:
            col_config = col_config_table.get_config(id)
            assert col_config
            result[id] = col_config.dict()
        else:
            for (_, collection_id, col_config) in col_config_table.get_all():
                assert collection_id
                result[collection_id] = col_config.dict()

    elif type == "container":
        con_config_table = ContainerConfigTable.from_sas_token(
            account_url=account_url, sas_token=sas, table_name=table
        )
        if id:
            con_account = kwargs.get("container_account")
            assert con_account
            con_config = con_config_table.get_config(con_account, id)
            assert con_config
            result[f"{con_account}/{id}"] = con_config.dict()
        else:
            for (storage_account, container, con_config) in con_config_table.get_all():
                result[f"{storage_account}/{container}"] = con_config.dict()
    else:
        print(f"Unknown type: {type}")
        return 1

    if output:
        with open(output, "w") as f:
            json.dump(result, f, indent=2)
    else:
        print(json.dumps(result, indent=2))

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

    def add_common_opts(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--sas",
            help="SAS Token for the storage account.",
            required=True,
        )
        p.add_argument("--account", help="Storage account name.", required=True)
        p.add_argument(
            "--table", help="Table name.", default=DEFAULT_COLLECTION_CONFIG_TABLE_NAME
        )
        p.add_argument(
            "-t",
            "--type",
            help="Type of configuration.",
            choices=["collection", "container"],
            required=True,
        )

    # collection config commands
    parser = subparsers.add_parser(
        "load",
        help="Load config into a storage table",
        parents=[parent],
        formatter_class=dhf,
    )
    parser.add_argument(
        "--file", help="Filename to load collection configuration from.", required=True
    )
    add_common_opts(parser)

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

    add_common_opts(parser)

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

    return 2


if __name__ == "__main__":
    return_code = cli()
    if return_code and return_code != 0:
        sys.exit(return_code)
