"""Setup for pcstac."""

from setuptools import find_packages, setup

# Runtime requirements.
inst_reqs = [
    "stac-fastapi.types==2.3.0",
    "stac-fastapi.api==2.3.0",
    "stac-fastapi.extensions==2.3.0",
    "stac-fastapi.pgstac==2.3.0",
    "pystac==1.*",
    "pccommon",
    # TODO: remove, pypgstac is not really needed to run stac-fastapi application
    "pypgstac==0.4.3",
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
