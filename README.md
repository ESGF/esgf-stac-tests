# esgf-stac-tests

An idea of how we could setup end-to-end tests for the ESGF STAC infrastructure.

If you are using `uv` you can clone this repository and issue:

```
uv run pytest
```

which should return:

```
========================================= test session starts ==========================================
platform linux -- Python 3.13.1, pytest-8.4.1, pluggy-1.6.0 -- /home/nate/work/esgf-stac-tests/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/nate/work/esgf-stac-tests
configfile: pyproject.toml
testpaths: ./
collected 8 items                                                                                      

test_stac.py::test_filters[api.stac.esgf.ceda.ac.uk-filter0-56] PASSED                            [1/8]
test_stac.py::test_filters[api.stac.esgf.ceda.ac.uk-filter1-56] PASSED                            [2/8]
test_stac.py::test_filters[api.stac.esgf.ceda.ac.uk-filter2-2] PASSED                             [3/8]
test_stac.py::test_filters[data-challenge-04-discovery.api.stac.esgf-west.org-filter0-56] PASSED  [4/8]
test_stac.py::test_filters[data-challenge-04-discovery.api.stac.esgf-west.org-filter1-56] PASSED  [5/8]
test_stac.py::test_filters[data-challenge-04-discovery.api.stac.esgf-west.org-filter2-2] PASSED   [6/8]
test_stac.py::test_asset_extra_fields[api.stac.esgf.ceda.ac.uk] PASSED                            [7/8]
test_stac.py::test_asset_extra_fields[data-challenge-04-discovery.api.stac.esgf-west.org] FAILED  [8/8]

===================================== 1 failed, 7 passed in 4.73s ======================================
```
