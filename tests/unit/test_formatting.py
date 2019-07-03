import sys
import os

import pytest


@pytest.mark.skipif(sys.version_info < (3, 6), reason="requires Python3")
def test_code_style():
    from pathlib import Path
    import black
    from click.testing import CliRunner

    root = str(Path(__file__).parent.parent.parent)

    runner = CliRunner()
    resp = runner.invoke(
        black.main,
        [
            "--check",
            os.path.join(root, "tests"),
            os.path.join(root, "spinningjenny"),
            os.path.join(root, "setup.py"),
            "--exclude",
            "spinningjenny/version.py",  # File written by setuptools_scm
        ],
    )

    assert (
        resp.exit_code == 0
    ), "Black would still reformat one or ore files:\n{}".format(resp.output)
