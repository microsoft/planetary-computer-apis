from typing import Any, Dict, List, Optional


def recursive_itemfix(schema: Any) -> None:
    try:
        if isinstance(schema["items"], list):
            schema["items"] = schema["items"][0]
    except KeyError:
        pass

    try:
        for anyOf in schema["anyOf"]:
            recursive_itemfix(anyOf)
    except KeyError:
        pass

    for _, v in schema.items():
        if isinstance(v, dict):
            recursive_itemfix(v)


def fix_openapi_output(openapi_dict: Dict) -> None:
    for _, path_definition in openapi_dict["paths"].items():
        try:
            del path_definition["get"]["requestBody"]
        except KeyError:
            pass

        try:
            for param in path_definition["get"]["parameters"]:
                if "exclusiveMaximum" in param["schema"]:
                    param["schema"]["maximum"] = param["schema"]["exclusiveMaximum"]
                    param["schema"]["minimum"] = param["schema"]["exclusiveMinimum"]
                    param["schema"]["exclusiveMaximum"] = True
                    param["schema"]["exclusiveMinimum"] = True
        except KeyError:
            pass

    for _, schema in openapi_dict["components"]["schemas"].items():
        try:
            for _, schema_props in schema["properties"].items():
                recursive_itemfix(schema_props)
        except KeyError:
            pass


def set_root_path(root_path: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    def _append_root_path(k: str) -> str:
        # Only prepend root_path if it's not already included in the server's URL
        if all(
            root_path not in server.get("url", "")
            for server in schema.get("servers", [])
        ):
            return f"{root_path}{k}"
        return k

    return {
        **{k: v for k, v in schema.items() if k != "paths"},
        "paths": {_append_root_path(k): v for k, v in schema["paths"].items()},
    }


def filter_paths(schema: Dict[str, Any], filter_out_tags: List[str]) -> Dict[str, Any]:
    """Filters untagged routes, or any route that is included in filter_tags.

    Also filters out deprecated routes."""
    paths_to_include = set([])
    for path, methods in schema["paths"].items():
        for _, definition in methods.items():
            include = True
            if "deprecated" in definition:
                if definition["deprecated"]:
                    include = False
            if "tags" in definition:
                for tag in definition["tags"]:
                    if tag in filter_out_tags:
                        include = False
            else:
                include = False

            if include:
                paths_to_include.add(path)

    return {
        **{k: v for k, v in schema.items() if k != "paths"},
        "paths": {k: v for k, v in schema["paths"].items() if k in paths_to_include},
    }


def remove_unused_components(schema: Dict[str, Any]) -> None:
    skip_components = ["HTTPValidationError", "ValidationError"]
    components = schema["components"]["schemas"]
    for component in list(components.keys()):
        if component in skip_components:
            del components[component]
        if component.startswith("stac_api__models__"):
            del components[component]

    paths = schema["paths"]
    for path in paths.values():
        for op in path.values():
            if "422" in op["responses"]:
                del op["responses"]["422"]


def add_tag(schema: Dict[str, Any], tag: str) -> None:
    """Adds a tag to the paths of the given schema"""
    for path_ops in schema.get("paths", {}).values():
        for op in path_ops.values():
            if "tags" not in op:
                op["tags"] = []
            if tag not in op["tags"]:
                op["tags"].append(tag)


def fixup_schema(
    root_path: str, schema: Dict[str, Any], tag: Optional[str] = None
) -> Dict[str, Any]:
    fix_openapi_output(schema)
    remove_unused_components(schema)
    if tag:
        add_tag(schema, tag)
    return filter_paths(
        set_root_path(root_path, schema), filter_out_tags=["Liveliness/Readiness"]
    )
