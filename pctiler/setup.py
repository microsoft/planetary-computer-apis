"""Setup for pctiler."""

from setuptools import find_packages, setup

# Runtime requirements.
inst_reqs = [
    "geojson-pydantic==0.3.3",
    "jinja2==3.0.3",
    "pystac==1.*",
    "planetary-computer==0.4.*",

    "rasterio==1.2.*",
    "titiler.core==0.5.*",
    "titiler.mosaic==0.5.*",

    # titiler-pgstac
    "psycopg[binary,pool]",
    "titiler.pgstac==0.1.0a7",

    # colormap dependencies
    "matplotlib==3.4.*",

    "importlib_resources>=1.1.0;python_version<'3.9'",
    "pccommon",
]

extra_reqs = {
    "test": [
        "pytest",
        "pytest-asyncio",
        "httpx",
    ],
    "dev": [
        "pytest",
        "pytest-asyncio",
    ],
    # server deps
    "server": [
        "uvicorn[standard]>=0.12.0,<0.16.0",
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
