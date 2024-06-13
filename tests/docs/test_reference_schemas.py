import importlib
import sys
from pathlib import Path

import pytest


@pytest.mark.slow
def test_doc_schemas(reference_docs: Path, tmp_path: Path):
    spec = importlib.util.spec_from_file_location(
        "doc_schemas", reference_docs / "doc_schemas.py"
    )
    my_script = importlib.util.module_from_spec(spec)
    sys.modules["doc_schemas"] = my_script
    spec.loader.exec_module(my_script)

    my_script.main(["--output-directory", str(tmp_path)])
    assert any(tmp_path.iterdir())
    assert (
        temp.read_bytes() == docs.read_bytes()
        for temp, docs in zip(
            tmp_path.glob("**/*.yml"), reference_docs.glob("**/*.yml")
        )
    )
