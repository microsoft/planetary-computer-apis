"""Setup for pcstac."""

from setuptools import find_packages, setup

# Runtime requirements.
inst_reqs = [
    "orjson==3.5.2",
    "cachetools==4.2.1",

    # TODO: remove. stac_fastapi Installed from source
    # Including upgrade for pgStac 0.4.0
    # Remove after release >2.2.0
    "stac_fastapi.types @ git+https://github.com/stac-utils/stac-fastapi.git@a1e32cb3d32d3a7f031275296b98309b0c6be1cf#subdirectory=stac_fastapi/types",
    "stac_fastapi.api @ git+https://github.com/stac-utils/stac-fastapi.git@a1e32cb3d32d3a7f031275296b98309b0c6be1cf#subdirectory=stac_fastapi/api",
    "stac_fastapi.extensions @ git+https://github.com/stac-utils/stac-fastapi.git@a1e32cb3d32d3a7f031275296b98309b0c6be1cf#subdirectory=stac_fastapi/extensions",
    "stac_fastapi.pgstac @ git+https://github.com/stac-utils/stac-fastapi.git@a1e32cb3d32d3a7f031275296b98309b0c6be1cf#subdirectory=stac_fastapi/pgstac",
    # "stac-fastapi.types==2.2.0",
    # "stac-fastapi.api==2.2.0",
    # "stac-fastapi.extensions==2.2.0",
    # "stac-fastapi.pgstac==2.2.0",

    "fastapi==0.67.*",
    "pystac==1.*",
    "pccommon",  # Planetary Computer Commons

    # TODO: remove. pypgstac is a `test/dev` dependency but
    # the way CI is designed we have to install it by default
    "pypgstac==0.4.0",
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
    name="pcstac",
    python_requires=">=3.7",
    description="Planetary Computer API - STAC.",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
