from setuptools import setup

setup(
    name="ubridge",
    version="1.1.0",
    description="Cross-language integer fixed-point serialization bridge natively resolving IEEE 754 drift.",
    author="Smokey-setup",
    packages=["."],
    package_data={"": ["libubridge.so", "libubridge.dylib", "ubridge.dll"]},
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: C",
    ],
)
