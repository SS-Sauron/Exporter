from setuptools import setup

setup(
    name="exporter-cli",
    version="1.0.0",
    description="A safe, interactive file transfer utility for the terminal",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="SS-Sauron",
    url="https://github.com/SS-Sauron/Exporter",
    license="MIT",
    python_requires=">=3.8",          # ← missing! README says 3.8+ but setup.py doesn't enforce it
    py_modules=["exporter"],
    entry_points={
        "console_scripts": ["exporter=exporter:interactive_shell"],
    },
    install_requires=[],
    extras_require={"trash": ["send2trash"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Utilities",
    ],
)
