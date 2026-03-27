import pytest
import typer

from tools.admin_cli import validate_latitude, validate_longitude


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
