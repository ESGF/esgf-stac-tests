"""
Pytest configuration file for testing STAC endpoints.

This file defines pytest fixtures and hooks to support testing against multiple STAC endpoints.
It provides a command-line option `--stac-endpoints` to specify a comma-separated list of endpoints to test against.
Tests can be parameterized by STAC endpoints using the `PerEndpointSuite` class.
"""

import pytest

DEFAULT_STAC_ENDPOINTS: list[str] = [
    "https://api.stac.esgf.ceda.ac.uk",
    "https://data-challenge-04-discovery.api.stac.esgf-west.org",
]


def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Pytest hook to add the `--stac-endpoints` command-line option.

    This option allows users to specify a comma-separated list of STAC endpoints to test against.
    """
    group: pytest.OptionGroup = parser.getgroup("esgf", "ESGF STAC Tests Options")

    group.addoption(
        "--stac-endpoints",
        action="store",
        default=DEFAULT_STAC_ENDPOINTS,
        type=lambda x: x.split(","),
        help="Comma-separated list of STAC endpoints to test against.",
    )

    parser.addini("stac_endpoints", type="args", help="STAC endpoint URLs to test against.")


class PerEndpointSuite:
    """These tests are parameterized by STAC_ENDPOINTS in addition to their individual parameters."""


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """
    Pytest hook to parameterize tests for classes inheriting from PerEndpointSuite.

    This function checks if the test class is a subclass of PerEndpointSuite and
    parameterizes the test with the endpoint URLs provided through the
    `--stac-endpoints` command-line or ini options.
    """
    if metafunc.cls and issubclass(metafunc.cls, PerEndpointSuite):
        endpoint_urls = metafunc.config.getoption("--stac-endpoints")
        metafunc.parametrize("endpoint_url", endpoint_urls)
