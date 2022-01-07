"""Setup for pccommon."""

from setuptools import find_packages, setup

# Runtime requirements.
inst_reqs = [
    "fastapi",
    "opencensus-ext-azure==1.0.8",
    "opencensus-ext-logging==0.1.0",
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
