# Integration Test Results

Results from the [ESGF/esgf-stac-tests](https://github.com/ESGF/esgf-stac-tests)
suite run against west-discovery.

---

## 2026-09-01

**Endpoints:** `search-int.east.esgf.io` (east) and local west-discovery at
`http://localhost:8000/` (west, running the PR #39 datetime fix).

**Totals:** 42 cases (21 per endpoint) — **33 passed · 7 failed · 2 xfail.**
West (local): 16 pass / 4 fail / 1 xfail. East: 17 pass / 3 fail / 1 xfail.

**Change vs. previous run:** west 15 → 16 passing. The datetime fix (PR #39)
resolved `cmip6_temporal_by_datetime`.

| Test | East | West |
|---|---|---|
| searching_with_filters — var_id_eq_rsus_rsds | pass | pass |
| searching_with_filters — var_id_in_rsus_rsds | pass | pass |
| searching_with_filters — var_id_snw_source_id_E3SM-1-0 | pass | pass |
| searching_with_filters — member_id_eq_r4i1p1f1 | pass | pass |
| searching_with_filters — variant_label_eq_r4i1p1f1 | pass | pass |
| searching_with_filters — specific_node | pass | **fail** |
| searching_with_free_text — temperature | pass | pass |
| searching_with_free_text — wind_and_filter | pass | pass |
| assets_include_file_extention_attributes | pass | pass |
| pagination | pass | pass |
| validate_catalog | **fail** | **fail** |
| endpoint_uses_published_cmip6_extension | xfail | xfail |
| collections | **fail** | pass |
| aggregation_facet_frequency | pass | pass |
| aggregation_alt_name | pass | **fail** |
| cmip6_collection_geospatial_extent | pass | pass |
| cmip6_temporal_by_datetime | pass | **pass** (newly fixed) |
| cmip6_temporal_by_query | pass | pass |
| cmip6_temporal_by_filter | **fail** | **fail** |
| query_by_ids | pass | pass |
| searching_with_filters_from_first | pass | pass |

**Remaining west failures**

- `searching_with_filters[specific_node]` — `alternate:name` property not mapped
  to the index field for replica/host names; returns zero items.
- `aggregation_alt_name` — test requests `alternate_name_frequency`; west only
  defines `cmip6_alternate_name_frequency`. Needs an unprefixed alias.

**Shared / not-west**

- `validate_catalog` (east + west) - `validate_all()`, likely the `CMIP6Test`
  extension schema.
- `cmip6_temporal_by_filter` (both) — CQL2 `t_intersects` unimplemented.
- `endpoint_uses_published_cmip6_extension` (both) — expected failure (xfail).
- `collections` (east only) — not a west-discovery issue.
