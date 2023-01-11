"""Setup for pcstac."""

from setuptools import find_packages, setup

# Runtime requirements.
inst_reqs = [
    "stac-fastapi.api @ git+https://github.com/stac-utils/stac-fastapi/@25879afe94296eb82b94b523bfa2871b686e035a#egg=stac-fastapi.api&subdirectory=stac_fastapi/api",
    "stac-fastapi.extensions @ git+https://github.com/stac-utils/stac-fastapi/@25879afe94296eb82b94b523bfa2871b686e035a#egg=stac-fastapi.extensions&subdirectory=stac_fastapi/extensions",
    "stac-fastapi.pgstac @ git+https://github.com/stac-utils/stac-fastapi/@25879afe94296eb82b94b523bfa2871b686e035a#egg=stac-fastapi.pgstac&subdirectory=stac_fastapi/pgstac",
    "stac-fastapi.types @ git+https://github.com/stac-utils/stac-fastapi/@25879afe94296eb82b94b523bfa2871b686e035a#egg=stac-fastapi.types&subdirectory=stac_fastapi/types",
    "pccommon",
    # Required due to some imports related to pypgstac CLI usage in startup script
    "pypgstac[psycopg]==0.6.9",
    "pystac==1.*",
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
