from setuptools import setup, Extension

setup(
    name="ubridge",
    version="1.0.0",
    description="Cross-language data serialization bridge natively solving IEEE 754 drift via C-ABI memory routing",
    author="Smokey-setup",
    packages=["."],
    ext_modules=[Extension("libubridge", ["ubridge.c"])],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: C",
    ],
)
