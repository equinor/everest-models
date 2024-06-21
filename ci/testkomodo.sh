
install_test_dependencies () {
    pip install .[test]
}

start_tests () {
    python -m pytest --test-resinsight
}
