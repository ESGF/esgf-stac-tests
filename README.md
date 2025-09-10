# esgf-stac-tests

End-to-end testing of the ESGF STAC infrastructure. This repository of tests is meant to collect problems that were found while developing user interfaces. If you are developing an interface and find that something is not behaving as you expect, please:

1. raise an issue at the [ESGF Roadmap](https://github.com/ESGF/esgf-roadmap/issues) repository and add the `stac-search-api` label, and
2. create a test and submit via PR here so we can track that it gets fixed.

The CI will run periodically at midnight, but can also be triggered manually in "Actions". Click on the badge below to be taken to logs where you can see what exactly is not passing.

[![Continuous Integration][ci-badge]][ci-link]

## Installation/Running

If you are using [`uv`](https://docs.astral.sh/uv/getting-started/installation/) you can clone this repository and issue:

```
uv run pytest
```

