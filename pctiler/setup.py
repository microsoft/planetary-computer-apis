"""Setup for pctiler."""

from setuptools import find_packages, setup

# Runtime requirements.
inst_reqs = [
    "geojson-pydantic==0.3.1",
    "jinja2==2.11.3",
    "cachetools==4.2.1",
    "pystac==1.0.0-rc.2",
    "planetary-computer==0.3.0-rc.0",

    "rasterio==1.2.6",
    "titiler.core==0.4.*",
    "titiler.mosaic==0.4.*",

    # titiler-pgstac
    "psycopg[binary,pool]",
    "titiler.pgstac==0.1.0a3",

    # colormap dependencies
    "matplotlib==3.4.*",

    "importlib_resources>=1.1.0;python_version<'3.9'",
    "pccommon",
]

extra_reqs = {
    "test": [
        "pytest",
        "pytest-asyncio",
    ],
    "dev": [
        "pytest",
        "pytest-asyncio",
    ],
    # server deps
    "server": [
        "uvicorn[standard]==0.13.3",
        "uvloop==0.14.0",
        "gunicorn==20.1.0",
    ],
}

setup(
    name="pctiler",
    python_requires=">=3.7",
    description="Planetary Computer API - Tiler.",
    packages=find_packages(exclude=["tests"]),
    package_data={"pctiler": ["templates/*.html"]},
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
