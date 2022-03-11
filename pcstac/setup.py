"""Setup for pcstac."""

from setuptools import find_packages, setup

# Runtime requirements.
inst_reqs = [
    # "stac-fastapi.api==2.3.0",
    # "stac-fastapi.extensions==2.3.0",
    # "stac-fastapi.pgstac==2.3.0",
    # "stac-fastapi.types==2.3.0",
    "stac-fastapi.api @ git+https://github.com/stac-utils/stac-fastapi/@81015a153c1d9f36d8e12f17a1bf67370396f472#egg=stac-fastapi.api&subdirectory=stac_fastapi/api",
    "stac-fastapi.extensions @ git+https://github.com/stac-utils/stac-fastapi/@81015a153c1d9f36d8e12f17a1bf67370396f472#egg=stac-fastapi.extensions&subdirectory=stac_fastapi/extensions",
    "stac-fastapi.pgstac @ git+https://github.com/stac-utils/stac-fastapi/@81015a153c1d9f36d8e12f17a1bf67370396f472#egg=stac-fastapi.pgstac&subdirectory=stac_fastapi/pgstac",
    "stac-fastapi.types @ git+https://github.com/stac-utils/stac-fastapi/@81015a153c1d9f36d8e12f17a1bf67370396f472#egg=stac-fastapi.types&subdirectory=stac_fastapi/types",
    "pystac==1.*",
    "pccommon",
    # TODO: remove, pypgstac is not really needed to run stac-fastapi application
    "pypgstac==0.4.5",
]

extra_reqs = {
    "test": [
        "pytest",
        "pytest-asyncio",
        # for now pypgstac is in requirement.txt
        # "pypgstac==0.4.2",
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
