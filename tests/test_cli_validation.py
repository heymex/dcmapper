import pytest
import typer

from tools.admin_cli import validate_latitude, validate_longitude, validate_source


def test_validate_latitude_valid():
    assert validate_latitude(45.0) == 45.0


def test_validate_latitude_invalid():
    with pytest.raises(typer.BadParameter):
        validate_latitude(91.0)


def test_validate_longitude_valid():
    assert validate_longitude(-120.25) == -120.25


def test_validate_longitude_invalid():
    with pytest.raises(typer.BadParameter):
        validate_longitude(-181.0)


def test_validate_source_rejects_empty():
    with pytest.raises(typer.BadParameter):
        validate_source("   ")


def test_validate_source_accepts_https_url():
    assert validate_source("https://example.org/reference") == "https://example.org/reference"
