from setuptools import setup
from setuptools.dist import Distribution


class BinaryDistribution(Distribution):
    def has_ext_modules(self):
        return True


setup(
    name="ubridge",
    version="1.1.0",
    description="Cross-language integer fixed-point serialization bridge natively resolving IEEE 754 drift.",
    author="Smokey-setup",
    packages=["ubridge"],
    package_data={
        "ubridge": [
            "libubridge.so",
            "libubridge.dylib",
            "ubridge.dll"
        ]
    },
    include_package_data=True,
    distclass=BinaryDistribution,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: C",
    ],
)
