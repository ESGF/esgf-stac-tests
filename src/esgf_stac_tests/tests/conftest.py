"""
Pytest configuration file for testing STAC endpoints.

This file defines pytest fixtures and hooks to support testing against multiple STAC endpoints.
"""

import pytest

DEFAULT_STAC_ENDPOINTS: list[str] = [
    "https://api.stac.esgf.ceda.ac.uk",
    "https://data-challenge-04-discovery.api.stac.esgf-west.org",
]


def pytest_addoption(parser: pytest.Parser) -> None:
    """Pytest hook to add custom ini and command-line options."""
    group: pytest.OptionGroup = parser.getgroup("esgf", "ESGF STAC Tests Options")
    parser.addini("stac_endpoints", type="args", help="STAC endpoint URLs to test against.")

    group.addoption(
        "--stac-endpoints",
        action="store",
        default=DEFAULT_STAC_ENDPOINTS,
        type=lambda x: x.split(","),
        help="Comma-separated list of STAC endpoints to test against.",
    )

    group.addoption(
        "--data-challenge",
        action="store",
        default=0,
        type=int,
        help="Run tests with expectations for a specific Data Challenge (0-4).",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers and import Data Challenge specific plugins."""
    config.addinivalue_line("markers", "data_challenge(id): mark test as specific to a particular Data Challenge.")
    config.addinivalue_line("markers", "data_challenge_xfail(id): mark test as expected to fail for a particular Data Challenge.")
    config.addinivalue_line(
        "markers",
        "needed_for(client): mark test as validating functionality needed for a specific client (metagrid, esmvaltool, etc).",
    )

    config.pluginmanager.import_plugin("esgf_stac_tests.fixtures.default.conftest")

    data_challenge = config.getoption("--data-challenge")
    if data_challenge > 0:
        # Load fixtures from the `fixtures/data_challenge_X/conftest.py` if a non-zero data challenge is specified
        config.pluginmanager.import_plugin(f"esgf_stac_tests.fixtures.data_challenge_{data_challenge}.conftest")


@pytest.fixture(autouse=True)
def _(request: pytest.FixtureRequest) -> None:
    """XFail any test with the `data_challenge_xfail` marker, but only if that Data Challenge is activated."""
    xfail_marker = request.node.get_closest_marker("data_challenge_xfail")
    if xfail_marker is None:
        return

    if request.config.getoption("--data-challenge") == xfail_marker.args[0]:
        pytest.xfail(reason=xfail_marker.kwargs["reason"])


def pytest_report_header(config: pytest.Config) -> list[str] | None:
    """Add an indicator to the top of runs when a Data Challenge scenario is activated."""
    data_challenge = config.getoption("--data-challenge")
    if data_challenge > 0:
        return [f"Running tests with expectations for Data Challenge {data_challenge}"]
    return None


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Pytest hook to parameterize tests over the selected STAC endpoints."""
    if "endpoint_url" in metafunc.fixturenames:
        metafunc.parametrize("endpoint_url", metafunc.config.getoption("--stac-endpoints"))
