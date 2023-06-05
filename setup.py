from setuptools import setup

NAME = "solution"

setup(
    name=NAME,
    version="1.0.0",
    py_modules=[NAME],
    entry_points={
        "console_scripts": [
            f"{NAME}=solution:main",
        ],
    },
)
