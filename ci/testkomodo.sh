copy_test_files () {
    cp -r ${CI_SOURCE_ROOT}/tests ${CI_TEST_ROOT}/tests
    cp -r ${CI_SOURCE_ROOT}/docs ${CI_TEST_ROOT}/docs
}

install_test_dependencies () {
    pip install .[test]
}

start_tests () {
    python -m pytest --test-resinsight
}
