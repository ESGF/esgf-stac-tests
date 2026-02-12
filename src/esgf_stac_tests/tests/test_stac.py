"""Tests for STAC endpoints."""

import copy
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


def test_collections(endpoint_url: str, supported_collections: list[str]) -> None:
    """Check for expected collections."""
    client = pystac_client.Client.open(endpoint_url)
    assert set(supported_collections).issubset(
        [coll.id for coll in client.get_collections()],
    )


def test_facet_counts(endpoint_url: str) -> None:
    """Can we get facet counts.

    Note
    ----
    I don't think that pystac does aggregations so we will use search and then
    hack the url. This tests is a placeholder and needs improved as the
    capability grows.
    """
    client = pystac_client.Client.open(endpoint_url)
    results = client.search(
        collections=["CMIP6"],
        filter={
            "args": [{"property": "properties.cmip6:activity_id"}, "VolMIP"],
            "op": "=",
        },
    )
    url = results.url_with_parameters()
    url = url.replace(
        "search?",
        "aggregate?aggregations=cmip6_source_id_frequency,cmip6_table_id_frequency&",
    )
    response = requests.get(url)
    response.raise_for_status()
    content = response.json()
    out = {agg["name"]: [b["key"] for b in agg["buckets"]] for agg in content["aggregations"]}
    assert "cmip6_source_id_frequency" in out
    assert "cmip6_table_id_frequency" in out
    assert len(out["cmip6_source_id_frequency"]) > 0
    assert len(out["cmip6_table_id_frequency"]) > 0


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
        filter={
            "op": "t_intersects",
            "args": [{"property": "datetime"}, "1850-01-01/2015-01-01"],
        },
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
                "CMIP6.VolMIP.NERC.UKESM1-0-LL.volc-pinatubo-full.r3i1p1f2.SImon.siconca.gr.v20230810",
                "CMIP6.VolMIP.NERC.UKESM1-0-LL.volc-pinatubo-full.r27i1p1f2.Lmon.mrro.gn.v20230810",
            ],
        ).items_as_dicts(),
    )
    assert len(items) == 2


def test_collection_items(endpoint_url: str) -> None:
    """Test the items endpoint for a dataset in a collection."""
    dataset = "CMIP6.ScenarioMIP.MPI-M.MPI-ESM1-2-LR.ssp245.r5i1p1f1.3hr.tas.gn.v20190710"
    url = f"{endpoint_url}/collections/CMIP6/items/{dataset}"
    response = requests.get(url)
    assert response.status_code == 200, "No success response from STAC endpoint."
    body  = response.json()

    assert len(body["assets"]) == 6, "Expected 6 assets in response."


def test_compare_filter_and_filter_exp(endpoint_url: str) -> None:
    """See if the filter and filter_exp give the same results.

    Note
    ----
    Climate4impact used the filter on CEDA instead of the filter_exp. This gave the results we expected.
    After hearing we should use filter_exp because it had a name change we got different behavior.
    We preferred the behavior of filter.
    """
    url = f"{endpoint_url}/aggregate"

    stac_filter = {
            "op": "and",
            "args": [
                {
                    "op": "=",
                    "args": [
                        {"property": "cmip6:variable_id"},
                        "tas"
                    ]
                },
                {
                    "op": "=",
                    "args": [
                        {"property": "cmip6:frequency"},
                        "3hr"
                    ]
                }
            ]
        }

    payload = {
        "collections": ["CMIP6"],
        "sortBy": ["created"],
        "aggregations": ["cmip6_experiment_id_frequency"]
    }

    payload_filter = copy.deepcopy(payload)
    payload_filter_exp = copy.deepcopy(payload)

    payload_filter["filter"] = stac_filter
    payload_filter_exp["filter_exp"] = stac_filter


    response_filter = requests.post(url, json=payload_filter)
    body_filter = response_filter.json()

    response_filter_exp = requests.post(url,json=payload_filter_exp)
    body_filter_exp = response_filter_exp.json()

    assert body_filter == body_filter_exp


def test_aggregate_endpoint_uses_no_filter(endpoint_url: str) -> None:
    """To me it looks like the aggregate endpoint does not use the filter_exp.

    """
    url = f"{endpoint_url}/aggregate"


    stac_filter = {
            "op": "and",
            "args": [
                {
                    "op": "=",
                    "args": [
                        {"property": "cmip6:variable_id"},
                        "tas"
                    ]
                },
                {
                    "op": "=",
                    "args": [
                        {"property": "cmip6:frequency"},
                        "3hr"
                    ]
                },
                {
                    "op": "=",
                    "args": [
                        {"property": "cmip6:experiment_id"},
                        "ssp585"
                    ]
                }
            ]
        }

    payload = {
        "collections": ["CMIP6"],
        "sortBy": ["created"],
        "aggregations": ["cmip6_experiment_id_frequency"]
    }


    payload_filter = copy.deepcopy(payload)
    payload_no_filter = copy.deepcopy(payload)

    payload_filter["filter_exp"] = stac_filter

    response_filter = requests.post(url, json=payload_filter)
    body_filter = response_filter.json()

    response_no_filter = requests.post(url, json=payload_no_filter)
    body_no_filter = response_no_filter.json()

    assert body_filter == body_no_filter