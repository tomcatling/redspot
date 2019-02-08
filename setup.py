from pathlib import Path

from setuptools import setup, find_packages


def read_long_description() -> str:
    """Read from README.md file in root of source directory."""
    root = Path(__file__).resolve().parent
    readme = root / "README.md"
    return readme.read_text(encoding="utf-8")


setup(
    name="redspot",
    description="Tools for running Jupyter notebooks in the cloud.",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/tomcatling/redspot",
    author="Tom Catling",
    author_email="tomcatling@gmail.com",
    license="ISC",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Operating System :: Unix",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License (MIT)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(),
    include_package_data=True,
    use_scm_version={"version_scheme": "post-release"},
    setup_requires=["setuptools_scm"],
    python_requires=">3.6",
    install_requires=["click>=7.0"],
    entry_points={"console_scripts": ["redspot=redspot.cli:cli"]},
)
