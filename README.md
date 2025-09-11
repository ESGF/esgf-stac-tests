# esgf-stac-tests

End-to-end testing of the ESGF STAC infrastructure. This repository of tests is meant to collect problems that were found while developing user interfaces. If you are developing an interface and find that something is not behaving as you expect, please:

1. raise an issue at the [ESGF Roadmap](https://github.com/ESGF/esgf-roadmap/issues) repository and add the `stac-search-api` label, and
2. create a test and submit via PR here so we can track that it gets fixed.

[![Continuous Integration][ci-badge]][ci-link]

## Running the tests

### Ad-hoc
Using [`uvx`](https://docs.astral.sh/uv/guides/tools/) you can run the tests as a command without installing the package:

```shell
$ uvx git+https://github.com/nocollier/esgf-stac-tests.git
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
   $ uv add --dev git+https://github.com/nocollier/esgf-stac-tests.git
   ```
1. Inherit your test class from `TestStacEndpoints`:
    #### mypkg/tests/test_my_endpoint.py
    ```python
    import pytest
    from unittest.mock import patch
    from esgf_stac_tests.tests.test_stac import TestStacEndpoints


    class TestMyEndpoint(TestStacEndpoints):

        # Define a new test. It will be ran once for every
        # configured STAC endpoint
        def test_extra_tests_ran(endpoint_url: str):
            assert endpoint_url is not None

        # Override an existing test
        def test_validate_catalog(self, endpoint_url: str) -> None:
            with patch("my_module.that.breaks.the_test"):
                super().test_validate_catalog(self, endpoint_url)

        # All of the other existing tests will be ran as well

    ```
## Specifying endpoints to test
By default, the tests will be ran against the endpoints defined in [conftest.py](src/esgf_stac_tests/tests/conftest.py):
1. https://api.stac.esgf.ceda.ac.uk
1. https://data-challenge-04-discovery.api.stac.esgf-west.org

This can be overridden by passing a comma separated list of urls to the `--stac-endpoints` flag on the command line:
```shell
$ uvx git+https://github.com/nocollier/esgf-stac-tests.git --stac-endpoints "https://api.stac.esgf.ceda.ac.uk,https://data-challenge-04-discovery.api.stac.esgf-west.org"
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

[ci-badge]: https://github.com/nocollier/esgf-stac-tests/actions/workflows/ci.yml/badge.svg?branch=main
[ci-link]: https://github.com/nocollier/esgf-stac-tests/actions/workflows/ci.yml
