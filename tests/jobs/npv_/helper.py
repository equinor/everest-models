import os

_CONFIG_FILE = "input_data.yml"


def assert_written_npv(tmpdir, expected_npv, out_path):
    written_npv_output_file = os.path.join(tmpdir.strpath, out_path)
    assert os.path.isfile(written_npv_output_file)
    with open(written_npv_output_file, "r") as written_npv_output:
        assert float(written_npv_output.readline()) == expected_npv
