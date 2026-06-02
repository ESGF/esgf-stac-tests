"""Fixture overrides for Data Challenge 7 (intergration)."""

import pytest


@pytest.fixture
def expected_result_count(request: pytest.FixtureRequest) -> int:
    """Get the expected result count for the current filter search scenario."""
    result_counts: dict[str, int] = {
        "var_id_eq_rsus_rsds": 39,
        "var_id_in_rsus_rsds": 39,
        "var_id_snw_source_id_ACCESS-ESM1-5": 1,
        "member_id_eq_r4i1p1f1": 4,
        "variant_label_eq_r4i1p1f1": 4,
        "specific_node": 3,
        "temperature": 0,
        "wind_and_filter": 0,
        "variable_id_frequency": 0,
        "alternate_name_frequency": 0,
    }

    # Get the value of the "filter_scenario" parameter for the current test
    return result_counts[request.node.callspec.params["filter_scenario"]]
