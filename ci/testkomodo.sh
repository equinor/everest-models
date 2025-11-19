copy_test_files () {
    cp -r ${CI_SOURCE_ROOT}/tests ${CI_TEST_ROOT}/tests
    cp -r ${CI_SOURCE_ROOT}/docs ${CI_TEST_ROOT}/docs
}

install_test_dependencies () {
    python -c "import tomllib; \
deps = tomllib.load(open('pyproject.toml', 'rb'))\
['project']['optional-dependencies']['test'];\
print('\n'.join(deps))" > dev_requirements.txt
    pip install -r dev_requirements.txt
}

start_tests () {
    python -m pytest --test-resinsight
}
