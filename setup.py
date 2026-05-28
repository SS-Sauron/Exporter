from setuptools import setup

setup(
    name="exporter-cli",
    version="1.0.0",
    py_modules=["exporter"],
    entry_points={
        "console_scripts": [
            "exporter=exporter:interactive_shell",
        ],
    },
    install_requires=[],
    extras_require={"trash": ["send2trash"]},
)
