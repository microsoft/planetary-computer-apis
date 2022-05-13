"""Setup for pcstac."""

from setuptools import find_packages, setup

# Runtime requirements.
inst_reqs = [
    # "stac-fastapi.api==2.3.0",
    # "stac-fastapi.extensions==2.3.0",
    # "stac-fastapi.pgstac==2.3.0",
    # "stac-fastapi.types==2.3.0",
    # "stac-fastapi.api @ git+https://github.com/stac-utils/stac-fastapi/@81015a153c1d9f36d8e12f17a1bf67370396f472#egg=stac-fastapi.api&subdirectory=stac_fastapi/api",
    # "stac-fastapi.extensions @ git+https://github.com/stac-utils/stac-fastapi/@81015a153c1d9f36d8e12f17a1bf67370396f472#egg=stac-fastapi.extensions&subdirectory=stac_fastapi/extensions",
    # "stac-fastapi.pgstac @ git+https://github.com/stac-utils/stac-fastapi/@81015a153c1d9f36d8e12f17a1bf67370396f472#egg=stac-fastapi.pgstac&subdirectory=stac_fastapi/pgstac",
    # "stac-fastapi.types @ git+https://github.com/stac-utils/stac-fastapi/@81015a153c1d9f36d8e12f17a1bf67370396f472#egg=stac-fastapi.types&subdirectory=stac_fastapi/types",
    "stac-fastapi.api @ git+https://github.com/mmcfarland/stac-fastapi/@f6da7b13eb31f8ea466ddee07e2bbfed69b1ec26#egg=stac-fastapi.api&subdirectory=stac_fastapi/api",
    "stac-fastapi.extensions @ git+https://github.com/mmcfarland/stac-fastapi/@f6da7b13eb31f8ea466ddee07e2bbfed69b1ec26#egg=stac-fastapi.extensions&subdirectory=stac_fastapi/extensions",
    "stac-fastapi.pgstac @ git+https://github.com/mmcfarland/stac-fastapi/@f6da7b13eb31f8ea466ddee07e2bbfed69b1ec26#egg=stac-fastapi.pgstac&subdirectory=stac_fastapi/pgstac",
    "stac-fastapi.types @ git+https://github.com/mmcfarland/stac-fastapi/@f6da7b13eb31f8ea466ddee07e2bbfed69b1ec26#egg=stac-fastapi.types&subdirectory=stac_fastapi/types",
    "pystac==1.*",
    "pccommon",
    # "pypgstac[psycopg]==0.6.1",
    "pypgstac @ git+https://github.com/stac-utils/pgstac@18b738be8ab4eee1b355d1df9a023ef9e2a0e2bc#egg=pypgstac&subdirectory=pypgstac",
    "psycopg[binary]==3.0.*",
    "psycopg-pool==3.1.*",
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
