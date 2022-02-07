"""Setup for pccommon."""

from setuptools import find_packages, setup

# Runtime requirements.
with open("requirements.txt", "r") as f:
    inst_reqs = f.readlines()

extra_reqs = {
    "test": [
        "pytest",
        "pytest-asyncio",
    ],
    "dev": [
        "pytest",
        "pytest-asyncio",
    ],
}

setup(
    name="pccommon",
    python_requires=">=3.7",
    description="Planetary Computer API - Common.",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
