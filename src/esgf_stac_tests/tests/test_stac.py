"""Tests for STAC endpoints."""

import pystac_client
import pytest
import requests

from esgf_stac_tests.fixtures.default.conftest import (
    FilterScenario,
    FreeTextScenario,
)

class EmptyResultError(Exception):
    """A blank exception to raies in place of StopIteration when the catalog returns nothing."""

def test_searching_with_filters(
    endpoint_url: str, filter_scenario: FilterScenario, expected_result_count: int,
) -> None:
    """Verify that filtered searches return results."""
    client = pystac_client.Client.open(endpoint_url)
    try:
        page = next(
            iter(
                client.search(
                    collections="CMIP6", filter=filter_scenario["filter"],
                ).pages_as_dicts(),
            ),
        )
    except StopIteration as exc:
        raise EmptyResultError from exc
    assert page["numberMatched"] == expected_result_count


def test_searching_with_free_text(
    endpoint_url: str, free_text_scenario: FreeTextScenario, expected_result_count: int,
) -> None:
    """Verify that free text searches return results."""
    client = pystac_client.Client.open(endpoint_url)
    try:
        page = next(
            iter(
                client.search(
                    collections="CMIP6",
                    filter=free_text_scenario["filter"],
                    query=free_text_scenario["q"],
                ).pages_as_dicts(),
            ),
        )
    except StopIteration as exc:
        raise EmptyResultError from exc
    assert page["numberMatched"] == expected_result_count


def test_assets_include_file_extention_attributes(endpoint_url: str) -> None:
    """Verify Item Assets include the file:size and file:checksum attributes from the `file` STAC extension."""
    client = pystac_client.Client.open(endpoint_url)

    search_pages = client.search(collections="CMIP6").pages()
    first_page = next(search_pages)
    asset = list(
        first_page.items[0].get_assets(media_type="application/netcdf").values()
    )[0]

    assert "file:size" in asset.extra_fields
    assert "file:checksum" in asset.extra_fields


@pytest.mark.timeout(60)
def test_pagination(endpoint_url: str) -> None:
    """Verify that all results can be retrieved by paging through them."""
    client = pystac_client.Client.open(endpoint_url)

    search_pages = client.search(
        collections="CMIP6",
        filter={
                   "op": "and",
                   "args": [
                       {
                           "args": [{"property": "cmip6:variable_id"}, "rsus"],
                           "op": "=",
                       },
                       {
                           "args": [{"property": "cmip6:activity_id"}, "CMIP"],
                           "op": "=",
                       },
                   ],
               },
    ).pages_as_dicts()
    try:
        first_page = next(search_pages)
    except StopIteration as exc:
        raise EmptyResultError from exc

    expected_pages = int(first_page["numberMatched"] / first_page["numberReturned"])
    actual_pages = sum(1 for _ in search_pages)

    assert actual_pages == expected_pages


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
    assert (
        len(cmip6_extension) == 1
    ), f"Multiple possible cmip6 extensions found: {cmip6_extension}"
    cmip6_url = cmip6_extension[0]
    cmip6_schema = requests.get(cmip6_url).json()

    # Assertion on dicts will give a diff if they are not the same so we can see what changes were needed
    assert cmip6_schema == published_schema


def test_collections(endpoint_url: str, supported_collections: list[str]) -> None:
    """Check for expected collections."""
    client = pystac_client.Client.open(endpoint_url)
    assert set(supported_collections).issubset(
        [coll.title for coll in client.get_collections()],
    )


def test_aggregation_facet_frequency(endpoint_url: str) -> None:
    """Check that we can return counts of facets.

    Note
    ----
    I don't think that pystac does aggregations natively, so we will form a post
    request manually instead.
    """
    response = requests.post(
        f"{endpoint_url}/aggregate",
        json={
            "collections": ["CMIP6"],
            "filter_exp": {"args": [{"property": "cmip6:activity_id"}, "ScenarioMIP"], "op": "="},
            "aggregations": ["cmip6_source_id_frequency", "cmip6_table_id_frequency"],
        },
    )
    response.raise_for_status()
    content = response.json()
    out = {agg["name"]: [b["key"] for b in agg["buckets"]] for agg in content["aggregations"]}
    assert "cmip6_source_id_frequency" in out
    assert "cmip6_table_id_frequency" in out
    assert len(out["cmip6_source_id_frequency"]) > 0
    assert len(out["cmip6_table_id_frequency"]) > 0


def test_aggregation_alt_name(endpoint_url: str) -> None:
    """Check that we can get counts for `alternate_name_frequency`.

    Note
    ----
    I don't think that pystac does aggregations natively, so we will form a post
    request manually instead.
    """
    response = requests.post(
        f"{endpoint_url}/aggregate",
        json={
            "collections": ["CMIP6"],
            "filter_exp": {"args": [{"property": "cmip6:activity_id"}, "ScenarioMIP"], "op": "="},
            "aggregations": ["alternate_name_frequency"],
        },
    )
    response.raise_for_status()
    content = response.json()
    out = {agg["name"]: [b["key"] for b in agg["buckets"]] for agg in content["aggregations"]}
    assert "alternate_name_frequency" in out
    assert "esgf-data.nersc.gov" in out["alternate_name_frequency"]
    assert len(out["alternate_name_frequency"]) > 0


def test_cmip6_collection_geospatial_extent(endpoint_url: str) -> None:
    """Check for expected collections and print their descriptions.

    Note
    ----
    Test from Phil, it may be that this is handled in STAC's validate_all().
    """
    client = pystac_client.Client.open(endpoint_url)

    cmip6_coll = client.get_collection("CMIP6")

    cmip6_coll_extent = cmip6_coll.extent.to_dict()

    assert cmip6_coll_extent
    assert "spatial" in cmip6_coll_extent
    assert "temporal" in cmip6_coll_extent
    assert "bbox" in cmip6_coll_extent["spatial"]
    assert "interval" in cmip6_coll_extent["temporal"]


def test_cmip6_temporal_by_datetime(endpoint_url: str) -> None:
    """Can we get results using the datetime keyword.

    Note
    ----
    According to
    https://pystac-client.readthedocs.io/en/latest/api.html#item-search this
    should work.
    """
    client = pystac_client.Client.open(endpoint_url)
    item_search = client.search(
        collections=["CMIP6"],
        datetime="1850-01-01/2015-01-01",
        max_items=1,
    )
    item = next(item_search.items())
    assert item


def test_cmip6_temporal_by_query(endpoint_url: str) -> None:
    """Can we get results using a query (not recommended)."""
    client = pystac_client.Client.open(endpoint_url)
    item_search = client.search(
        collections=["CMIP6"],
        query=["start_datetime>=1850-01-01", "end_datetime<=2015-01-01"],
        max_items=1,
    )
    item = next(item_search.items())
    assert item


def test_cmip6_temporal_by_filter(endpoint_url: str) -> None:
    """Can we filter results using t_intersects."""
    client = pystac_client.Client.open(endpoint_url)
    item_search = client.search(
        collections=["CMIP6"],
        filter={"op": "t_intersects", "args": [{"property": "datetime"}, {"interval": ["1850-01-01T00:00:00Z", "2015-01-01T00:00:00Z"]}]},
        max_items=1,
    )
    item = next(item_search.items())
    assert item


def test_query_by_ids(endpoint_url: str) -> None:
    """Can you give STAC a list of ids."""
    client = pystac_client.Client.open(endpoint_url)
    items = list(
        client.search(
            collections=["CMIP6"],
            ids=[
                "CMIP6.CMIP.MOHC.UKESM1-1-LL.piControl.r1i1p1f2.Omon.umo.gn.v20220505",
                "CMIP6.DAMIP.CSIRO.ACCESS-ESM1-5.hist-GHG.r9i1p1f1.day.snw.gn.v20230705",
            ],
        ).items_as_dicts(),
    )
    assert len(items) == 2


def test_searching_with_filters_from_first(
    endpoint_url: str,
) -> None:
    """Create a filter from the first results and the verify we can search for it."""

    def _create_filter(endpoint_url: str):
        client = pystac_client.Client.open(endpoint_url)
        try:
            page = next(
                iter(
                    client.search(
                        collections="CMIP6",
                        max_items=1,
                    ).pages_as_dicts(),
                ),
            )
        except StopIteration as exc:
            raise EmptyResultError from exc
        properties = page["features"][0]["properties"]
        return {
            "op": "and",
            "args": [
                {"args": [{"property": "cmip6:variable_id"}, properties["cmip6:variable_id"]], "op": "="},
                {"args": [{"property": "cmip6:source_id"}, properties["cmip6:source_id"]], "op": "="},
            ],
        }

    client = pystac_client.Client.open(endpoint_url)
    try:
        page = next(
            iter(
                client.search(
                    collections="CMIP6",
                    filter=_create_filter(endpoint_url),
                ).pages_as_dicts(),
            ),
        )
    except StopIteration as exc:
        raise EmptyResultError from exc
    assert page["numberMatched"] > 0
