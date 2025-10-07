from pathlib import Path
from setuptools import setup

# Fallback setup.py for legacy installers.
# Modern builds use pyproject.toml (setuptools build backend).

README = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name="xlsx2csv-mergefill",
    version="1.0.1",
    description="Excel→CSV with merged-cell fill (cp932), simple API",
    long_description=README,
    long_description_content_type="text/markdown",
    author="abachan",
    author_email="aiba1114@cl.cilas.net",
    license="MIT",
    packages=[
        "xlsx2csv_mergefill",
    ],
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "openpyxl>=3.1.0",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
