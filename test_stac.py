from typing import Any

import pystac_client
import pytest

# We can define the endpoints we wish to test here...
STAC_ENDPOINTS = [
    "api.stac.esgf.ceda.ac.uk",
    "api.stac.esgf-west.org",
]

# ...and cql filters along with the number of items each should return.
FILTERS_WITH_COUNTS = [
    (
        {
            "op": "or",
            "args": [
                {
                    "args": [{"property": "properties.cmip6:variable_id"}, "rsus"],
                    "op": "=",
                },
                {
                    "args": [{"property": "properties.cmip6:variable_id"}, "rsds"],
                    "op": "=",
                },
            ],
        },
        56,
    ),  # ---------------------------------------------------
    (
        {
            "op": "in",
            "args": [{"property": "properties.cmip6:variable_id"}, ["rsus", "rsds"]],
        },
        56,
    ),  # ---------------------------------------------------
    (
        {
            "op": "and",
            "args": [
                {
                    "args": [{"property": "properties.cmip6:variable_id"}, "tas"],
                    "op": "=",
                },
                {
                    "args": [{"property": "properties.cmip6:source_id"}, "MIROC6"],
                    "op": "=",
                },
            ],
        },
        2,
    ),  # ---------------------------------------------------
]


# Using that information we parameterize a test over all combinations.
@pytest.mark.parametrize("filter,num_items", FILTERS_WITH_COUNTS)
@pytest.mark.parametrize("endpoint_url", STAC_ENDPOINTS)
def test_filters(endpoint_url: str, filter: dict[str, Any], num_items: int) -> None:
    """
    Perform a basic search with the specified filter and verify number of records.
    """
    client = pystac_client.Client.open(f"https://{endpoint_url}")
    page = next(iter(client.search(collections="CMIP6", filter=filter).pages()))
    assert page.extra_fields["numMatched"] == num_items


@pytest.mark.parametrize("endpoint_url", STAC_ENDPOINTS)
def test_asset_extra_fields(endpoint_url: str) -> None:
    """
    Grab the first item from the endpoint and see if there is checksum
    information present in the assets.
    """
    client = pystac_client.Client.open(f"https://{endpoint_url}")
    page = next(
        iter(
            client.search(
                collections="CMIP6",
                filter={
                    "op": "in",
                    "args": [
                        {"property": "properties.cmip6:variable_id"},
                        ["rsus", "rsds"],
                    ],
                },
            ).pages()
        )
    )
    item = next(iter(page))
    # Any asset just not the Kerchunk reference file
    asset = next(iter([a for key, a in item.assets.items() if key != "reference_file"]))
    assert "file:size" in asset.extra_fields
    assert "file:checksum" in asset.extra_fields
