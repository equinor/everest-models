
install_package () {
    pip install ruamel.yaml
    python setup.py install
}

start_tests () {
    python -m pip install --upgrade protobuf # needed as komodoenv broke protobuf package
    python -m pytest \
        --ignore="tests/unit/test_formatting.py"\
        --ignore="tests/unit/test_jobs_implementation.py"
}
