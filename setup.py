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
version_path = module_dir / "VERSION"
version = version_path.read_text(encoding="utf-8").strip()

data_files = [module_dir / "voices.json", version_path]

setup(
    name="yakyak",
    version="0.0.50",
    description="A utility for accessing Piper synthetic voice in Docker.",
    package_dir={"": "yakyak"},
    packages=find_packages(where="yakyak"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/b202i/yakyak",
    author="MakerMattDesign",
    author_email="matt@makermattdesign.com",
    license="MIT",
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
    keywords="Utility for wyoming-piper tts",
    install_requires=["bson >= 0.5.10"],
    extras_require={
        "dev": ["pytest>=7.0", "twine>=4.0.2"],
    },
    python_requires=">=3.7",
)
