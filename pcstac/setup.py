"""Setup for pcstac."""

from setuptools import find_packages, setup

# Runtime requirements.
inst_reqs = [
    "stac-fastapi.api @ git+https://github.com/stac-utils/stac-fastapi/@162a1a2c324b4c2bfe3451f7ae19d7840a0e0452#egg=stac-fastapi.api&subdirectory=stac_fastapi/api",
    "stac-fastapi.extensions @ git+https://github.com/stac-utils/stac-fastapi/@162a1a2c324b4c2bfe3451f7ae19d7840a0e0452#egg=stac-fastapi.extensions&subdirectory=stac_fastapi/extensions",
    "stac-fastapi.pgstac @ git+https://github.com/stac-utils/stac-fastapi/@162a1a2c324b4c2bfe3451f7ae19d7840a0e0452#egg=stac-fastapi.pgstac&subdirectory=stac_fastapi/pgstac",
    "stac-fastapi.types @ git+https://github.com/stac-utils/stac-fastapi/@162a1a2c324b4c2bfe3451f7ae19d7840a0e0452#egg=stac-fastapi.types&subdirectory=stac_fastapi/types",
    "pccommon",
    # Required due to some imports related to pypgstac CLI usage in startup script
    "pypgstac[psycopg]==0.6.2",
    "pystac==1.*",
]

extra_reqs = {
    "test": [
        "pytest",
        "pytest-asyncio",
    ],
    "dev": [
        "black==22.3.0",
        "flake8==3.8.4",
        "httpx==0.19.0",
        "isort==5.9.2",
        "mypy==0.800",
        "openapi-spec-validator==0.3.0",
    ],
    # server deps
    "server": [
        "uvicorn[standard]>=0.12.0,<0.16.0",
        "hypercorn>=0.13,<0.14",
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
