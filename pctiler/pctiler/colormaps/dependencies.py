# flake8: noqa

import json
from typing import Callable, List, Literal, Optional, Sequence, Union

from fastapi import HTTPException, Query
from rio_tiler.colormap import ColorMaps, parse_color
from rio_tiler.types import ColorMapType
from typing_extensions import Annotated


# Port of titiler.core.dependencies.create_colormap_dependency (0.18.3) which
# support case-sensitive keys in QueryParams and pydantic validation responses
def create_colormap_dependency(
    cmap: ColorMaps, original_casing_keys: List[str]
) -> Callable:
    """Create Colormap Dependency."""

    def deps(  # type: ignore
        colormap_name: Annotated[  # type: ignore
            Literal[tuple(original_casing_keys)],
            Query(description="Colormap name"),
        ] = None,
        colormap: Annotated[
            Optional[str], Query(description="JSON encoded custom Colormap")
        ] = None,
    ) -> Union[ColorMapType, None]:
        if colormap_name:
            return cmap.get(colormap_name.lower())

        if colormap:
            try:
                c = json.loads(
                    colormap,
                    object_hook=lambda x: {
                        int(k): parse_color(v) for k, v in x.items()
                    },
                )

                # Make sure to match colormap type
                if isinstance(c, Sequence):
                    c = [(tuple(inter), parse_color(v)) for (inter, v) in c]

                return c
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=400, detail="Could not parse the colormap value."
                ) from e

        return None

    return deps
