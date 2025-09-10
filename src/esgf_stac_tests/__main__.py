"""Run tests defined in this package.

Ran with either `python -m esgf_stac_tests` or `uvx esgf_stac_tests`,
this is a thin wrapper around pytest's own CLI that only discovers tests in this
package's base directory. This is accomplished by declaring `tests/**/*` as
`package-data` in pyproject.toml, which ensures that the tests are copied into the
base of the package's install directory. We then use pytest's `--pyargs` option to
tell it to look for tests in the package's directory. This way, running `pytest`
still works during development, but `uvx` can be used to run the tests without
installing the package locally.
"""

import sys

import pytest


def main() -> None:
    """Run the tests in this package. Inject the --pyargs option to limit test discovery to this package."""
    sys.argv = [sys.argv[0], "--pyargs", __package__, *sys.argv[1:]]
    raise SystemExit(pytest.console_main())


if __name__ == "__main__":
    main()
