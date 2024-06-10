"""Setup for pcstac."""

from setuptools import find_packages, setup

# Runtime requirements.
inst_reqs = [
    "idna>=3.7.0",
    "stac-fastapi.api==2.4.8",
    "stac-fastapi.extensions==2.4.8",
    "stac-fastapi.pgstac==2.4.9",
    "stac-fastapi.types==2.4.8",
    "orjson==3.10.4",
    # Required due to some imports related to pypgstac CLI usage in startup script
    "pypgstac[psycopg]~=0.7",
    "pystac==1.10.1",
]

extra_reqs = {
    "server": [
        "uvicorn[standard]>=0.17.0,<0.18.0",
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
