"""Tests for STAC endpoints."""

import copy
import pystac_client
import pytest
import requests

from esgf_stac_tests.fixtures.default.conftest import (
    FilterScenario,
    FreeTextScenario,
)

TEST_COLLECTION = "CMIP6Test"


class EmptyResultError(Exception):
    """A blank exception to raise in place of StopIteration when the catalog returns nothing."""


def test_searching_with_filters(
    endpoint_url: str,
    filter_scenario: FilterScenario,
    expected_result_count: int,
) -> None:
    """Verify that filtered searches return results."""
    client = pystac_client.Client.open(endpoint_url)
    try:
        page = next(
            iter(
                client.search(
                    collections=TEST_COLLECTION,
                    filter=filter_scenario["filter"],
                ).pages_as_dicts(),
            ),
        )
    except StopIteration as exc:
        raise EmptyResultError from exc
    assert page["numberMatched"] == expected_result_count


def test_searching_with_free_text(
    endpoint_url: str,
    free_text_scenario: FreeTextScenario,
    expected_result_count: int,
) -> None:
    """Verify that free text searches return results."""
    client = pystac_client.Client.open(endpoint_url)
    try:
        page = next(
            iter(
                client.search(
                    collections=TEST_COLLECTION,
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

    search_pages = client.search(collections=TEST_COLLECTION).pages()
    first_page = next(search_pages)
    asset = list(first_page.items[0].get_assets(media_type="application/netcdf").values())[0]

    assert "file:size" in asset.extra_fields
    assert "file:checksum" in asset.extra_fields


@pytest.mark.timeout(60)
def test_pagination(endpoint_url: str) -> None:
    """Verify that all results can be retrieved by paging through them."""
    client = pystac_client.Client.open(endpoint_url)

    search_pages = client.search(
        collections=TEST_COLLECTION,
        filter={
            "op": "and",
            "args": [
                {
                    "args": [{"property": "cmip6:frequency"}, "mon"],
                    "op": "=",
                },
                {
                    "args": [{"property": "cmip6:variable_units"}, "W m-2"],
                    "op": "=",
                },
                {
                    "args": [{"property": "cmip6:member_id"}, "r19i2p2f1"],
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


def test_endpoint_uses_published_cmip6_extension(endpoint_url: str) -> None:
    """
    Check that the endpoint is using the published STAC CMIP6 extension.

    Note
    ----
    This is more to help us understand when differences in test results could be
    because an endpoint is pointing to a different extension.
    """
    published_schema_url = "https://esgf.github.io/stac-transaction-api/cmip6test/v2.0.2/schema.json"

    client = pystac_client.Client.open(endpoint_url)
    response = client.search(collections=TEST_COLLECTION, max_items=1)
    extensions = response.item_collection_as_dict()["features"][0]["stac_extensions"]

    if published_schema_url in extensions:
        return  # All good, using the published extension

    published_schema = requests.get(published_schema_url).json()

    cmip6_extension = [url for url in extensions if TEST_COLLECTION in url]
    assert cmip6_extension, "No CMIP6 STAC extension found."
    assert len(cmip6_extension) == 1, f"Multiple possible cmip6 extensions found: {cmip6_extension}"
    cmip6_url = cmip6_extension[0]
    cmip6_schema = requests.get(cmip6_url).json()

    # Assertion on dicts will give a diff if they are not the same so we can see what changes were needed
    assert cmip6_schema == published_schema


def test_collections(endpoint_url: str, supported_collections: list[str]) -> None:
    """Check for expected collections."""
    client = pystac_client.Client.open(endpoint_url)
    assert {c.lower() for c in supported_collections}.issubset(
        [coll.id.lower() for coll in client.get_collections()],
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
            "collections": [TEST_COLLECTION],
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
            "collections": [TEST_COLLECTION],
            "filter_exp": {"args": [{"property": "cmip6:activity_id"}, "ScenarioMIP"], "op": "="},
            "aggregations": ["alternate_name_frequency"],
        },
    )
    response.raise_for_status()
    content = response.json()
    out = {agg["name"]: [b["key"] for b in agg["buckets"]] for agg in content["aggregations"]}
    assert "alternate_name_frequency" in out
    assert "eagle.alcf.anl.gov" in out["alternate_name_frequency"]
    assert len(out["alternate_name_frequency"]) > 0


def test_cmip6_collection_geospatial_extent(endpoint_url: str) -> None:
    """Check for expected collections and print their descriptions.

    Note
    ----
    Test from Phil, it may be that this is handled in STAC's validate_all().
    """
    client = pystac_client.Client.open(endpoint_url)

    cmip6_coll = client.get_collection(TEST_COLLECTION)

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
        collections=[TEST_COLLECTION],
        datetime="1850-01-01/2015-01-01",
        max_items=1,
    )
    item = next(item_search.items())
    assert item


def test_cmip6_temporal_by_query(endpoint_url: str) -> None:
    """Can we get results using a query (not recommended)."""
    client = pystac_client.Client.open(endpoint_url)
    item_search = client.search(
        collections=[TEST_COLLECTION],
        query=["start_datetime>=1850-01-01", "end_datetime<=2015-01-01"],
        max_items=1,
    )
    item = next(item_search.items())
    assert item


@pytest.mark.skip("STAC does not yet implement")
def test_cmip6_temporal_by_filter(endpoint_url: str) -> None:
    """Can we filter results using t_intersects."""
    client = pystac_client.Client.open(endpoint_url)
    item_search = client.search(
        collections=[TEST_COLLECTION],
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
            collections=[TEST_COLLECTION],
            ids=[
                "CMIP6Test.ScenarioMIP.UCSB.E3SM-1-0.ssp370.r19i2p2f1.Amon.hfls.gr.v20250312",
                "CMIP6Test.ScenarioMIP.UCSB.E3SM-1-0.ssp370.r19i2p2f1.Amon.clwvi.gr.v20250312",
            ],
        ).items_as_dicts(),
    )
    assert len(items) == 2


def test_searching_with_filters_from_first(
    endpoint_url: str,
) -> None:
    """Create a filter from the first results from each collection and verify we can search for it."""

    def _get_first_item(endpoint_url: str, collection: str) -> str:
        client = pystac_client.Client.open(endpoint_url)
        try:
            page = next(
                iter(
                    client.search(
                        collections=collection,
                        max_items=1,
                    ).pages_as_dicts(),
                ),
            )
        except StopIteration as exc:
            raise EmptyResultError from exc
        return str(page["features"][0]["id"])

    client = pystac_client.Client.open(endpoint_url)
    for col in client.get_all_collections():
        # Is there an item published for this collection?
        try:
            item_id = _get_first_item(endpoint_url, str(col))
        except EmptyResultError:
            continue
        # Now can we search for it?
        try:
            page = next(
                iter(
                    client.search(
                        collections=str(col),
                        id=item_id,
                    ).pages_as_dicts(),
                ),
            )
        except StopIteration as exc:
            raise EmptyResultError from exc
        if page["numberMatched"] != 1:
            raise ValueError(f"{col=} {page['numberMatched']=} != 1")


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

def test_aggregate_endpoint_with_filter_gives_400_with_different_error_body_for_east_and_west(
        endpoint_url: str) -> None:
    """To me it looks like it's a python error

    Note
    ----
    Climate4impact when stil using the same filter expression on CEDA as before the changes I now the an error.
    On west I also get an error but the format of the message is different. Should those not be the same?
    """
    url = f"{endpoint_url}/aggregate"

    stac_filter_1 = {
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

    payload_filter_1 = copy.deepcopy(payload)

    payload_filter_1["filter"] = stac_filter_1

    response_filter_1 = requests.post(url, json=payload_filter_1)
    body_filter_1 = response_filter_1.json()

    if endpoint_url == "https://data-challenge-04-discovery.api.stac.esgf-west.org":
        assert body_filter_1 == {
            'code': 'AttributeError',
            'description': "'tuple' object has no attribute 'lstrip'"
        }
    elif endpoint_url == "https://api.stac.esgf.ceda.ac.uk":
        assert body_filter_1 == {'detail': 'Error with cql2 filter: dictionary changed size during iteration'}