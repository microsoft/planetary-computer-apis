import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from pccommon.constants import DEFAULT_COLLECTION_CONFIG_TABLE_NAME
from pccommon.config.collections import CollectionConfigTable, CollectionConfig
from pccommon.config.containers import ContainerConfigTable, ContainerConfig
from pccommon.version import __version__


def load(sas: str, account: str, table: str, type: str, file: str) -> int:
    account_url = f"https://{account}.table.core.windows.net"
    with open(file) as f:
        rows = json.load(f)

    if type == "collection":
        config_table = CollectionConfigTable.from_sas_token(
            account_url=account_url, sas_token=sas, table_name=table
        )
        for coll_id, config in rows.items():
            config_table.set_config(coll_id, CollectionConfig(**config))

    elif type == "container":
        config_table = ContainerConfigTable.from_sas_token(
            account_url=account_url, sas_token=sas, table_name=table
        )
        for path, config in rows.items():
            storage_account, container = path.split("/")
            config_table.set_config(
                storage_account, container, ContainerConfig(**config)
            )
    else:
        print(f"Unknown type: {type}")
        return 1

    return 0


def dump(sas: str, account: str, table: str, type: str, **kwargs: Any) -> int:
    output = kwargs.get("output")
    account_url = f"https://{account}.table.core.windows.net"
    result: Dict[str, Dict[str, Any]] = {}
    if type == "collection":
        config_table = CollectionConfigTable.from_sas_token(
            account_url=account_url, sas_token=sas, table_name=table
        )

        for (_, collection_id, config) in config_table.get_all():
            result[collection_id] = config.dict()

    elif type == "container":
        config_table = ContainerConfigTable.from_sas_token(
            account_url=account_url, sas_token=sas, table_name=table
        )
        for (storage_account, container, config) in config_table.get_all():
            result[f"{storage_account}/{container}"] = config.dict()
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
    add_common_opts(parser)

    parsed_args = {
        k: v for k, v in vars(parser0.parse_args(args)).items() if v is not None
    }
    if "command" not in parsed_args:
        parser0.print_usage()
        return None

    return parsed_args


def cli():
    args = parse_args(sys.argv[1:])
    if not args:
        return None

    cmd = args.pop("command")

    if cmd == "load":
        return load(**args)
    elif cmd == "dump":
        return dump(**args)


if __name__ == "__main__":
    return_code = cli()
    if return_code and return_code != 0:
        sys.exit(return_code)
