"""Setup for pccommon."""

from setuptools import find_packages, setup

# Runtime requirements.
inst_reqs = [
    "fastapi==0.90.1",
    "starlette>=0.22.0,<0.23.0",
    "opencensus-ext-azure==1.0.8",
    "opencensus-ext-logging==0.1.0",
    "orjson>=3.9.15",
    "azure-identity==1.7.1",
    "azure-data-tables==12.4.0",
    "azure-storage-blob>=12.19.1",
    "pydantic>=1.9, <2.0.0",
    "cachetools~=5.3",
    "types-cachetools==4.2.9",
    "pyhumps==3.5.3",
    "redis==4.2.0-rc1",
    "html-sanitizer==1.9",
    "urllib3>=1.26.6",
]

extra_reqs = {
    "test": ["pytest", "pytest-asyncio", "types-redis"],
    "dev": ["pytest", "pytest-asyncio", "types-redis"],
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
    entry_points={"console_scripts": ["pcapis=pccommon.cli:cli"]},
)
