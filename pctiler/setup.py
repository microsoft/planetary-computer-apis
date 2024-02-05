"""Setup for pctiler."""

from typing import List
from setuptools import find_packages, setup

# Runtime requirements, see environment.yaml
inst_reqs: List[str] = []

extra_reqs = {
    "dev": ["types-requests"],
    "server": [
        "uvicorn[standard]>=0.17.0,<0.18.0",
    ],
}

setup(
    name="pctiler",
    python_requires=">=3.7",
    description="Planetary Computer API - Tiler.",
    packages=find_packages(exclude=["tests"]),
    package_data={"pctiler": ["endpoints/templates/*.html"]},
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
