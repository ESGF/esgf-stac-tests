"""Tests for STAC endpoints."""

import pystac_client
import pytest
import requests

from esgf_stac_tests.fixtures.default.conftest import FilterScenario


def test_searching_with_filters(endpoint_url: str, filter_scenario: FilterScenario, expected_result_count: int) -> None:
    """Verify that filtered searches return results."""
    client = pystac_client.Client.open(endpoint_url)
    page = next(iter(client.search(collections="CMIP6", filter=filter_scenario["filter"]).pages_as_dicts()))
    assert page["numMatched"] == expected_result_count


def test_assets_include_file_extention_attributes(endpoint_url: str) -> None:
    """Verify Item Assets include the file:size and file:checksum attributes from the `file` STAC extension."""
    client = pystac_client.Client.open(endpoint_url)

    search_pages = client.search(collections="CMIP6").pages()
    first_page = next(search_pages)
    asset = first_page.items[0].get_assets(media_type="application/netcdf")["data0001"]

    assert "file:size" in asset.extra_fields
    assert "file:checksum" in asset.extra_fields


@pytest.mark.timeout(60)
def test_pagination(endpoint_url: str) -> None:
    """Verify that all results can be retrieved by paging through them."""
    client = pystac_client.Client.open(endpoint_url)

    search_pages = client.search(
        collections="CMIP6",
        filter={
            "op": "in",
            "args": [
                {"property": "properties.cmip6:variable_id"},
                ["rsus", "rsds"],
            ],
        },
    ).pages_as_dicts()
    first_page = next(search_pages)

    expected_pages = int(first_page["numMatched"] / first_page["numReturned"])
    actual_pages = sum(1 for _ in search_pages)

    assert actual_pages == expected_pages


@pytest.mark.xfail(reason="CMIP6 STAC extension used is not public")
def test_validate_catalog(endpoint_url: str) -> None:
    """Validate the STAC catalog for the endpoint against the STAC spec."""
    pystac_client.Client.open(endpoint_url).validate_all()


@pytest.mark.xfail(reason="Temporary design decision")
@pytest.mark.data_challenge_xfail(4, reason="Temporary design decision")
def test_endpoint_uses_published_cmip6_extension(endpoint_url: str) -> None:
    """
    Check that the endpoint is using the published STAC CMIP6 extension.

    Note
    ----
    This is more to help us understand when differences in test results could be
    because an endpoint is pointing to a different extension.
    """
    published_schema_url = "https://stac-extensions.github.io/cmip6/v2.0.0/schema.json"

    client = pystac_client.Client.open(endpoint_url)
    response = client.search(collections="CMIP6", max_items=1)
    extensions = response.item_collection_as_dict()["features"][0]["stac_extensions"]

    if published_schema_url in extensions:
        return  # All good, using the published extension

    published_schema = requests.get(published_schema_url).json()

    cmip6_extension = [url for url in extensions if "cmip6" in url]
    assert cmip6_extension, "No CMIP6 STAC extension found."
    assert len(cmip6_extension) == 1, f"Multiple possible cmip6 extensions found: {cmip6_extension}"
    cmip6_url = cmip6_extension[0]
    cmip6_schema = requests.get(cmip6_url).json()

    # Assertion on dicts will give a diff if they are not the same so we can see what changes were needed
    assert cmip6_schema == published_schema
