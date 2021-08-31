from typing import Any, Dict

# TODO: Pull out into common for usage with DQE and MQE


def recursive_itemfix(schema: Any) -> None:
    try:
        if type(schema["items"]) == list:
            schema["items"] = schema["items"][0]
    except KeyError:
        pass

    try:
        for anyOf in schema["anyOf"]:
            recursive_itemfix(anyOf)
    except KeyError:
        pass

    for _, v in schema.items():
        if type(v) == dict:
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
        return f"{root_path}{k}"

    return {
        **{k: v for k, v in schema.items() if k != "paths"},
        "paths": {_append_root_path(k): v for k, v in schema["paths"].items()},
    }
