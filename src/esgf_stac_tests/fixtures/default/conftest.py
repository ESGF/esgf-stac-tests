"""Fixtures used by the test suite.

If a Data Challenge is activated with the `--data-challenge` flag,
these fixtures will be overridden by any same-named fixtures defined
in `fixtures/data_challenge_X/conftest.py`
"""

from typing import TypedDict

import pytest
from pystac_client.item_search import FilterLike


class NonZero(int):
    """Comparator that matches any integer greater than zero."""

    __hash__ = int.__hash__

    def __eq__(self, other: object) -> bool:
        """Match any positive integer."""
        return (
            other > 0
        )  # pyright: ignore[reportOperatorIssue] -- other is object, but we only expect int here


CQL_FILTERS: dict[str, FilterLike] = {
    "var_id_eq_rsus_rsds": {
        "op": "or",
        "args": [
            {
                "args": [{"property": "cmip6:variable_id"}, "rsus"],
                "op": "=",
            },
            {
                "args": [{"property": "cmip6:variable_id"}, "rsds"],
                "op": "=",
            },
        ],
    },
    # ---------------------------------------------------
    "var_id_in_rsus_rsds": {
        "op": "in",
        "args": [{"property": "cmip6:variable_id"}, ["rsus", "rsds"]],
    },
    # ---------------------------------------------------
    "var_id_snw_source_id_ACCESS-ESM1-5": {
        "op": "and",
        "args": [
            {
                "args": [{"property": "cmip6:variable_id"}, "snw"],
                "op": "=",
            },
            {
                "args": [{"property": "cmip6:source_id"}, "ACCESS-ESM1-5"],
                "op": "=",
            },
        ],
    },
    # ---------------------------------------------------
    "member_id_eq_r4i1p1f1": {
        "args": [{"property": "cmip6:member_id"}, "r4i1p1f1"],
        "op": "=",
    },
    # ---------------------------------------------------
    "variant_label_eq_r4i1p1f1": {
        "args": [{"property": "cmip6:variant_label"}, "r4i1p1f1"],
        "op": "=",
    },
    # ---------------------------------------------------
    "specific_node": {
        "op": "=",
        "args": [{"property": "alternate:name"}, "ceda.ac.uk"],
    },
    # ---------------------------------------------------
}

FREE_TEXT_FILTERS: dict[str, dict] = {
    "temperature": {"q": ["temperature"]},
    # ---------------------------------------------------
    "wind_and_filter": {
        "q": ["wind"],
        "filter": {"op": "=", "args": [{"property": "properties.latest"}, "true"]},
    },
    # ---------------------------------------------------
}


class FilterScenario(TypedDict):
    """Named search filter."""

    name: str
    filter: FilterLike


class FreeTextScenario(TypedDict):
    """Free-text search query."""

    name: str
    q: list[str]
    filter: FilterLike


@pytest.fixture(params=CQL_FILTERS)
def filter_scenario(request: pytest.FixtureRequest) -> FilterScenario:
    """Parameterize each test with each filter scenario in `CQL_FILTERS`."""
    # Create a scenario name to filter mapping
    return {"name": request.param, "filter": CQL_FILTERS[request.param]}


@pytest.fixture(params=FREE_TEXT_FILTERS)
def free_text_scenario(request: pytest.FixtureRequest) -> FreeTextScenario:
    """Parameterize each test with each free-text scenario in `FREE_TEXT_FILTERS`."""
    # Create a scenario name to filter mapping
    return {
        "name": request.param,
        "q": FREE_TEXT_FILTERS[request.param].get("q"),
        "filter": FREE_TEXT_FILTERS[request.param].get("filter"),
    }


@pytest.fixture
def expected_result_count() -> int:
    """Get the expected result count for the current filter search scenario."""
    # Outside of specfic data challenges, we only care that SOME results were returned
    return NonZero()


@pytest.fixture
def supported_collections() -> list[str]:
    """Return the collections that should be supported."""
    return ["CMIP6"]
