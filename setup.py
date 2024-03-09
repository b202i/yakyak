#!/usr/bin/env python3
from pathlib import Path
from setuptools import find_packages, setup

with open("./README.md", "r") as f:
    long_description = f.read()

this_dir = Path(__file__).parent

requirements = []
requirements_path = this_dir / "requirements.txt"
if requirements_path.is_file():
    with open(requirements_path, "r", encoding="utf-8") as requirements_file:
        requirements = requirements_file.read().splitlines()

module_name = "yakyak"
module_dir = this_dir / module_name

setup(
    name=module_name,
    version='0.5.4',
    description="Utility for generating synthetic voice with Wyoming-Piper.",
    packages=find_packages(),
    install_requires=requirements,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/b202i/yakyak",
    author="MakerMattDesign",
    author_email="matt@makermattdesign.com",
    license="MIT",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Text Processing :: Linguistic",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    keywords="utility synthetic-voice wyoming-piper tts",
    entry_points={
        'console_scripts': [
            'yakyak = yakyak.__main__:main',
        ]
    },
)
