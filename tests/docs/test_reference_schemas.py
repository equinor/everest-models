import filecmp
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
    for doc in tmp_path.glob("**/*.yml"):
        relative_path = doc.relative_to(tmp_path)
        assert filecmp.cmp(reference_docs / relative_path, doc, shallow=False)
