"""Smoke test: the package imports and exposes a version. Keeps CI green pre-app."""

from terraform_intentions import __version__


def test_version_is_exposed() -> None:
    assert __version__ == "0.1.0"
