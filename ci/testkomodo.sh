
install_package () {
    pip install .[test]
}

start_tests () {
    python -m pytest --test-resinsight
}
