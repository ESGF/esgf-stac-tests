from typing import Any

import pystac
import pystac_client
import pytest
import requests

# We can define the endpoints we wish to test here...
STAC_ENDPOINTS = [
    "api.stac.esgf.ceda.ac.uk",
    "data-challenge-04-discovery.api.stac.esgf-west.org",
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
    (
        {
            "args": [{"property": "properties.cmip6:member_id"}, "r2i1p1f1"],
            "op": "=",
        },
        19,
    ),  # ---------------------------------------------------
    (
        {
            "args": [{"property": "properties.cmip6:variant_label"}, "r2i1p1f1"],
            "op": "=",
        },
        22,
    ),  # ---------------------------------------------------
]

# Which collections do we expect the API to find?
SUPPORTED_COLLECTIONS = ["CMIP6"]

# Which time ranges do we check?
TIME_RANGES = [("1850-01-01", "2020-01-01")]


# Using that information we parameterize a test over all combinations.
@pytest.mark.parametrize("filter,num_items", FILTERS_WITH_COUNTS)
@pytest.mark.parametrize("endpoint_url", STAC_ENDPOINTS)
def test_filters(endpoint_url: str, filter: dict[str, Any], num_items: int) -> None:
    """
    Perform a basic search with the specified filter and verify number of records.
    """
    client = pystac_client.Client.open(f"https://{endpoint_url}")
    page = next(
        iter(client.search(collections="CMIP6", filter=filter).pages_as_dicts())
    )
    assert page["numMatched"] == num_items


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
    asset = next(iter([a for key, a in item.assets.items() if "reference" not in key]))
    assert "file:size" in asset.extra_fields
    assert "file:checksum" in asset.extra_fields


@pytest.mark.parametrize("endpoint_url", STAC_ENDPOINTS)
def test_paging(endpoint_url: str) -> None:
    """
    Ensure correct number of pages when iterating.
    """
    client = pystac_client.Client.open(f"https://{endpoint_url}")
    expected_pages = None
    num_pages = 0
    for page in client.search(
        collections="CMIP6",
        filter={
            "op": "in",
            "args": [
                {"property": "properties.cmip6:variable_id"},
                ["rsus", "rsds"],
            ],
        },
    ).pages():
        num_pages += 1
        expected_pages = (
            (
                int(page.extra_fields["numMatched"] / page.extra_fields["numReturned"])
                + 1
            )
            if expected_pages is None
            else expected_pages
        )
    assert num_pages == expected_pages


@pytest.mark.xfail(reason="Temporary design decision")
@pytest.mark.parametrize("endpoint_url", STAC_ENDPOINTS)
def test_which_cmip6_extension(endpoint_url: str) -> None:
    """
    Check that the endpoint is using the correct STAC CMIP6 extension.

    Note
    ----
    This is more to help us understand when differences in test results could be
    because an endpoint is pointing to a different extension.
    """
    client = pystac_client.Client.open(f"https://{endpoint_url}")
    response = client.search(collections="CMIP6", max_items=1)
    item = response.item_collection_as_dict()["features"][0]
    cmip6_extension = [url for url in item["stac_extensions"] if "cmip6" in url]
    if not cmip6_extension:
        raise ValueError("No CMIP6 STAC extension found.")
    if not (cmip6_extension[0]).startswith("https://stac-extensions.github.io/cmip6/"):
        raise ValueError(f"Not using the standard CMIP6 extension: {cmip6_extension}")


@pytest.mark.parametrize("endpoint_url", STAC_ENDPOINTS)
def test_collections(endpoint_url: str) -> None:
    """
    Check for expected collections.
    """
    client = pystac_client.Client.open(f"https://{endpoint_url}")

    assert set(SUPPORTED_COLLECTIONS).issubset(
        [coll.id for coll in client.get_collections()]
    )


@pytest.mark.parametrize("endpoint_url", STAC_ENDPOINTS)
def test_cmip6_collection_geospatial_extent(endpoint_url: str) -> None:
    """
    Check for expected collections and print their descriptions.
    """
    client = pystac_client.Client.open(f"https://{endpoint_url}")

    cmip6_coll = client.get_collection("CMIP6")

    cmip6_coll_extent = cmip6_coll.extent.to_dict()

    assert cmip6_coll_extent
    assert "spatial" in cmip6_coll_extent
    assert "temporal" in cmip6_coll_extent
    assert "bbox" in cmip6_coll_extent["spatial"]
    assert "interval" in cmip6_coll_extent["temporal"]


@pytest.mark.parametrize("time_filter_method", ["datetime", "query", "filter"])
@pytest.mark.parametrize("time_range", TIME_RANGES)
@pytest.mark.parametrize("endpoint_url", STAC_ENDPOINTS)
def test_cmip6_temporal_query(
    endpoint_url: str, time_range: tuple[str, str], time_filter_method: str
) -> None:
    """
    Can we filter out records by a time filter of any sort?

    Note
    ----
    I cannot seem to make this work for either endpoint. It may be a problem
    with publishing?
    """
    time_start, time_end = time_range
    args = dict(
        datetime=f"{time_start}/{time_end}",
        query=[f"start_datetime>{time_start}", f"end_datetime<{time_end}"],
        filter={
            "op": "t_intersects",
            "args": [
                {"property": "start_datetime"},
                f"{time_start}/{time_end}",
            ],
        },
    )
    client = pystac_client.Client.open(f"https://{endpoint_url}")
    item_search = client.search(
        collections=["CMIP6"],
        max_items=1,
        **{time_filter_method: args[time_filter_method]},
    )
    next(iter(item_search.items()))


@pytest.mark.parametrize("endpoint_url", STAC_ENDPOINTS)
def test_item_content(endpoint_url: str) -> None:
    """
    Check that we can harvest an asset url.
    """
    client = pystac_client.Client.open(f"https://{endpoint_url}")
    item_search = client.search(collections=["CMIP6"], max_items=1)
    item = next(iter(item_search.items()))
    assert isinstance(item, pystac.item.Item)
    nc_assets = [v.href for _, v in item.assets.items() if v.href.endswith(".nc")]
    assert len(nc_assets) > 0
    nc_file_url = nc_assets[0]
    assert nc_file_url


@pytest.mark.parametrize("endpoint_url", STAC_ENDPOINTS)
def test_facet_counts(endpoint_url: str) -> None:
    """
    Can we get facet counts?

    Note
    ----
    I don't think that pystac does aggregations so we will use search and then
    hack the url. This tests is a placeholder and needs improved as the
    capability grows.
    """
    client = pystac_client.Client.open(f"https://{endpoint_url}")
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
    out = {
        agg["name"]: [b["key"] for b in agg["buckets"]]
        for agg in content["aggregations"]
    }

    assert len(out["cmip6_source_id_frequency"]) == 5
    assert len(out["cmip6_table_id_frequency"]) == 13
