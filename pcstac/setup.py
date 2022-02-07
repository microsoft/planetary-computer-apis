"""Setup for pcstac."""

from setuptools import find_packages, setup

# Runtime requirements.
with open("requirements.txt", "r") as f:
    inst_reqs = f.read()

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
