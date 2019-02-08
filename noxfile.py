"""Nox configuration."""

import nox

SOURCES = ["noxfile.py", "redspot", "tests"]


@nox.session()
def mypy(session):
    """Type check code with mypy."""
    session.install("mypy")
    session.run("mypy", "--strict", "redspot")


@nox.session()
def flake8(session):
    """Lint code with Flake8."""
    session.install("flake8")
    session.run("flake8", *SOURCES)


@nox.session()
def black(session):
    """Check code formatting with black."""
    session.install("black==18.9b0")
    if session.posargs:
        session.run("black", *session.posargs)
    else:
        session.run("black", "--check", *SOURCES)
