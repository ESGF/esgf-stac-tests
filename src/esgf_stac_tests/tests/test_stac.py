"""Tests for STAC endpoints."""

import pystac_client
import pytest
import requests
from pystac_client.item_search import FilterLike

from esgf_stac_tests.tests.conftest import PerEndpointSuite

# ...and cql filters along with the number of items each should return.
CQL_FILTERS: list[FilterLike] = [
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
    # ---------------------------------------------------
    {
        "op": "in",
        "args": [{"property": "properties.cmip6:variable_id"}, ["rsus", "rsds"]],
    },
    # ---------------------------------------------------
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
    # ---------------------------------------------------
    {
        "args": [{"property": "properties.cmip6:member_id"}, "r2i1p1f1"],
        "op": "=",
    },
    # ---------------------------------------------------
    {
        "args": [{"property": "properties.cmip6:variant_label"}, "r2i1p1f1"],
        "op": "=",
    },
    # ---------------------------------------------------
]


class TestStacEndpoints(PerEndpointSuite):
    """Tests for all STAC endpoints.

    In addition to their individual parameters, these tests are automatically
    parameterized by endpoint_url by the parent class.

    The `--stac-endpoints` command line option or the `stac_endpoints` ini option can be
    used to specify a comma-separated list of endpoints to test against. The default
    endpoints are defined in conftest.py.
    """

    @pytest.mark.parametrize("search_filter", CQL_FILTERS)
    def test_searching_with_filters(self, endpoint_url: str, search_filter: FilterLike) -> None:
        """Verify that filtered searches return results."""
        client = pystac_client.Client.open(endpoint_url)
        page = next(iter(client.search(collections="CMIP6", filter=search_filter).pages_as_dicts()))
        assert page["numMatched"] > 0

    def test_assets_include_file_extention_attributes(self, endpoint_url: str) -> None:
        """Verify Item Assets include the file:size and file:checksum attributes from the `file` STAC extension."""
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
        ).pages()
        first_page = next(search_pages)
        asset = first_page.items[0].get_assets(media_type="application/netcdf")["data0001"]

        assert "file:size" in asset.extra_fields
        assert "file:checksum" in asset.extra_fields

    @pytest.mark.timeout(60)
    def test_pagination(self, endpoint_url: str) -> None:
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

    def test_validate_catalog(self, endpoint_url: str) -> None:
        """Validate the STAC catalog for the endpoint against the STAC spec."""
        pystac_client.Client.open(endpoint_url).validate_all()

    def test_endpoint_uses_published_cmip6_extension(self, endpoint_url: str) -> None:
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
