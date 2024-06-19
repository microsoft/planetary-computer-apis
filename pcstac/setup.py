"""Setup for pcstac."""

from setuptools import find_packages, setup

# Runtime requirements.
inst_reqs = [
    "idna>=3.7.0",
    "stac-fastapi.api==3.0.0a3",
    "stac-fastapi.extensions==3.0.0a3",
    "stac-fastapi.pgstac==3.0.0a2",
    "stac-fastapi.types==3.0.0a3",
    "orjson==3.10.4",
    # Required due to some imports related to pypgstac CLI usage in startup script
    "pypgstac[psycopg]>=0.8.5,<0.9",
    "pystac==1.10.1",
    "typing_extensions>=4.6.1",
]

extra_reqs = {
    "server": [
        "uvicorn[standard]==0.30.1",
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
