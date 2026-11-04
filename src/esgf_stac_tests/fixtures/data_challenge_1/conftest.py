"""Fixture overrides for Data Challenge 1."""

import pytest


@pytest.fixture
def expected_result_count(request: pytest.FixtureRequest) -> int:
    """Get the expected result count for the current filter search scenario."""
    result_counts: dict[str, int] = {
        "var_id_eq_rsus_rsds": 301,
        "var_id_in_rsus_rsds": 301,
        "var_id_snw_source_id_E3SM-1-0": 20,
        "member_id_eq_r4i1p1f1": 169,
        "variant_label_eq_r4i1p1f1": 169,
    }

    # Get the value of the "filter_scenario" parameter for the current test
    return result_counts[request.node.callspec.params["filter_scenario"]]
