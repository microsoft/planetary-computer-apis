"""Setup for pccommon."""

from setuptools import find_packages, setup

# Runtime requirements.
inst_reqs = [
    "fastapi-slim==0.111.0",
    "starlette>=0.37.2,<0.38.0",
    "opencensus-ext-azure==1.1.13",
    "opencensus-ext-logging==0.1.1",
    "orjson>=3.10.4",
    "azure-identity==1.16.1",
    "azure-data-tables==12.5.0",
    "azure-storage-blob>=12.20.0",
    "pydantic>=2.7,<2.8.0",
    "pydantic-settings>=2.3,<2.4",
    "cachetools~=5.3",
    "types-cachetools==4.2.9",
    "pyhumps==3.5.3",
    "redis==4.6.0",
    "requests==2.32.3",
    "idna>=3.7.0",
    "html-sanitizer==2.4.4",
    # Soon available as lxml[html_clean]
    "lxml_html_clean==0.1.0",
    "urllib3>=1.26.18",
]

extra_reqs = {
    "test": ["pytest", "pytest-asyncio", "types-redis", "types-requests"],
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
