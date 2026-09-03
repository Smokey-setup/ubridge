import os
import re
from setuptools import setup, find_packages
from setuptools.dist import Distribution

class BinaryDistribution(Distribution):
    """Force wheel builder to treat this as a platform-specific binary distribution."""
    def has_ext_modules(self):
        return True

# 1. Dynamically read the long description from README.md
here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = ""

# 2. Dynamically extract version from ubridge/__init__.py
def get_version():
    init_path = os.path.join(here, "ubridge", "__init__.py")
    try:
        with open(init_path, "r", encoding="utf-8") as f:
            match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
            if match:
                return match.group(1)
    except FileNotFoundError:
        pass
    return "2.0.0"  # Upgraded fallback version reflecting the Universal Mathematical Operating Layer

setup(
    name="ubridge",
    version=get_version(),
    description="Universal Mathematical Operating Layer resolving IEEE 754 float drift, zero-copy atomic SPSC shared memory IPC, and hybrid precision across polyglot microservices.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Smokey-setup",
    
    # 3. Dynamically find packages instead of hardcoding ["ubridge"]
    packages=find_packages(include=["ubridge", "ubridge.*"]),
    
    package_data={
        # 4. Dynamically match any binary shared libraries in the package directory
        "ubridge": ["*.so", "*.dylib", "*.dll"]
    },
    include_package_data=True,
    distclass=BinaryDistribution,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: C",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
    ],
)
