# esgf-stac-tests

End-to-end testing of the ESGF STAC infrastructure. This repository of tests is meant to collect problems that were found while developing user interfaces. If you are developing an interface and find that something is not behaving as you expect, please:

1. raise an issue at the [ESGF Roadmap](https://github.com/ESGF/esgf-roadmap/issues) repository and add the `stac-search-api` label, and
2. create a test and submit via PR here so we can track that it gets fixed.

[![Continuous Integration][ci-badge]][ci-link]

[ci-badge]: https://github.com/ESGF/esgf-stac-tests/actions/workflows/ci.yml/badge.svg?branch=main
[ci-link]: https://github.com/ESGF/esgf-stac-tests/actions/workflows/ci.yml

## Running the tests

### Ad-hoc
Using [`uvx`](https://docs.astral.sh/uv/guides/tools/) you can run the tests as a command without installing the package:

```shell
$ uvx git+https://github.com/ESGF/esgf-stac-tests.git
================================================== test session starts ==================================================
platform linux -- Python 3.13.7, pytest-8.4.2, pluggy-1.6.0
rootdir: /home/zp0/projects
plugins: timeout-2.4.0
collected 20 items

tests/test_stac.py ............ss......                                                                           [100%]
============================================ 18 passed, 2 skipped in 16.00s =============================================
```
## CI
The CI will run at midnight each day, but can also be triggered manually in "Actions".

## As part of your own `pytest` suite
1. Add esgf-stac-tests as a dev dependency to your project:
   ```shell
   $ uv add --dev git+https://github.com/ESGF/esgf-stac-tests.git
   ```
1. Include the tests in your test paths, either:
   - on the command line:
   ```shell
   $ pytest --pyargs esgf_stac_tests.tests
   ```
   - or in your `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
    addopts = [
        "--pyargs=esgf_stac_tests.tests",
    ]
   ```

## Specifying endpoints to test
By default, the tests will be ran against the endpoints defined in [conftest.py](src/esgf_stac_tests/tests/conftest.py):
1. https://api.stac.esgf.ceda.ac.uk
1. https://data-challenge-04-discovery.api.stac.esgf-west.org

This can be overridden by passing a comma separated list of urls to the `--stac-endpoints` flag on the command line:
```shell
$ uvx git+https://github.com/ESGF/esgf-stac-tests.git --stac-endpoints "https://api.stac.esgf.ceda.ac.uk,https://data-challenge-04-discovery.api.stac.esgf-west.org"
```
or by setting the pytest `stac_endpoints` ini_option in `pyproject.toml`:
```toml
[project]
name = "myproject"
version = "0.1.0"
...
[tool.pytest.ini_options]
addopts = "--verbose"
stac_endpoints = [
    # ESGF East
    "https://data-challenge-04-discovery.api.stac.esgf-west.org",
    # ESGF West
    "https://api.stac.esgf.ceda.ac.uk",
    # Your custom endpoint
    "https://stac.yourdomain.com"
]
```
## Specifying a Data Challenge
Some tests are only relevant to a particular Data Challenge or have specific desired reults that don't apply outside that Data Challenge. The desired Data Challenge can be specified with `--data-challenge=N` where `N` is the Data Challenge number.

# Contributing
## Custom Markers
The following custom markers are defined:
- `@data_challenge(id)`: Tests marked with this will only run when the Data Challenge `id` is specified
- `@data_challenge_xfail(id)`: These tests are expected to fail during the given Data Challenge
- `@needed_for(client)`: Marks the test as testing functionality required by the given client
## Data Challenge Specific overrides
If a Data Challenge scenario requires different fixtures from the default, they can be defined in `fixtures/data_challenge_N/conftest.py` and they will be imported and take precedence over the default fixtures with the same name (those defined in [fixtures/default/conftest.py](src/esgf_stac_tests/fixtures/default/conftest.py))

For example, [test_searching_with_filters](tests/test_stac.py?#L10) tests searching endpoints with various filters. In the base case, the number of returned results will depend on what data is in the endpoint's associated index, so we use a [fixture that compares positively to any non-zero int](src/esgf_stac_tests/fixtures/default/conftest.py?#78-82).

In Data Challenge 4 however, we know the documents in the index so we can be more specific about the desired results. The `expected_result_count` fixture is redefined in the [Data Challenge specific fixtures](src/esgf_stac_tests/fixtures/data_challenge_4/conftest.py?#L4=16) so that it takes precedence over the default `expected_result_count` fixture when the `--data-challenge` flag is set to `4`. The logic for this lives in [src/esgf_stac_tests/tests/conftest.py](src/esgf_stac_tests/tests/conftest.py?#52-57)