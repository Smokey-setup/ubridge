import os
import re
from pathlib import Path

from setuptools import find_packages, setup
from setuptools.dist import Distribution


class BinaryDistribution(Distribution):
    """
    Mark the distribution as platform-specific because uBridge
    contains native C shared libraries.
    """

    def has_ext_modules(self):
        return True


HERE = Path(__file__).resolve().parent


def read_readme():
    """
    Load README.md when present.
    """
    readme = HERE / "README.md"

    if not readme.is_file():
        return ""

    return readme.read_text(encoding="utf-8")


def get_version():
    """
    Read the package version from ubridge/__init__.py.

    A missing or malformed version is a packaging error and must
    fail the build rather than silently producing an incorrect
    release.
    """

    init_path = HERE / "ubridge" / "__init__.py"

    if not init_path.is_file():
        raise RuntimeError(
            "Cannot determine ubridge version: "
            "ubridge/__init__.py is missing."
        )

    content = init_path.read_text(encoding="utf-8")

    match = re.search(
        r"^__version__\s*=\s*[\"']([^\"']+)[\"']\s*$",
        content,
        re.MULTILINE,
    )

    if not match:
        raise RuntimeError(
            "Cannot determine ubridge version: "
            "__version__ is missing from ubridge/__init__.py."
        )

    version = match.group(1).strip()

    if not version:
        raise RuntimeError(
            "Cannot determine ubridge version: "
            "__version__ is empty."
        )

    return version


setup(
    name="ubridge",
    version=get_version(),

    description=(
        "Universal Mathematical Operating Layer with deterministic "
        "serialization, fixed-point numeric handling, scientific "
        "precision, cyclic graph support, and a hardened native C ABI."
    ),

    long_description=read_readme(),
    long_description_content_type="text/markdown",

    author="Smokey-setup",
    license="MIT",

    packages=find_packages(
        include=[
            "ubridge",
            "ubridge.*",
        ]
    ),

    include_package_data=True,

    package_data={
        "ubridge": [
            "*.so",
            "*.dylib",
            "*.dll",
        ]
    },

    distclass=BinaryDistribution,

    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: C",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
    ],

    python_requires=">=3.9",
)
