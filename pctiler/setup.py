"""Setup for pctiler."""

from typing import List
from setuptools import find_packages, setup

# Runtime requirements, see environment.yaml
inst_reqs: List[str] = [
    "geojson-pydantic==0.4.2",
    "jinja2==3.1.4",
    "pystac==1.10.1",
    "planetary-computer==0.4.9",
    "rasterio==1.3.10",
    "titiler.core==0.10.2",
    "titiler.mosaic==0.10.2",
    "pillow==10.3.0",
    "boto3==1.34.136",
    "botocore==1.34.136",
    "pydantic==1.10.14",
    "idna>=3.7.0",
    "requests==2.32.2",
    # titiler-pgstac
    "psycopg[binary,pool]",
    "titiler.pgstac==0.2.4",
    # colormap dependencies
    "matplotlib==3.9.0",
    "orjson==3.10.4",
    "importlib_resources>=1.1.0;python_version<'3.9'",
]

extra_reqs = {
    "dev": ["types-requests"],
    "server": [
        "uvicorn[standard]>=0.17.0,<0.18.0",
    ],
}

setup(
    name="pctiler",
    python_requires=">=3.7",
    description="Planetary Computer API - Tiler.",
    packages=find_packages(exclude=["tests"]),
    package_data={"pctiler": ["endpoints/templates/*.html"]},
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
