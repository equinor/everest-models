
install_package () {
    pip install ruamel.yaml
    python setup.py install
}

start_tests () {
    python -m pip install --upgrade protobuf # needed as komodoenv broke protobuf package
    # For unknown reasons the many_wells_one_ring hangs on Jenkins
    python -m pytest \
        -k "not test_many_wells_one_rig" \
        --ignore="tests/unit/test_formatting.py"\
        --ignore="tests/unit/test_jobs_implementation.py"
}
