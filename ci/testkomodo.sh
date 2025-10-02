copy_test_files () {
    cp -r ${CI_SOURCE_ROOT}/tests ${CI_TEST_ROOT}/tests
    cp -r ${CI_SOURCE_ROOT}/docs ${CI_TEST_ROOT}/docs
}

install_test_dependencies () {
    pip install .[test]
}

# Run everest eightcells test on the cluster
run_everest_eightcells_test() {

    if [[ "$CI_RUNNER_LABEL" == "azure" ]]; then
        #RUNNER_ROOT="/lustre1/users/f_scout_ci/eightcells_tests"
        echo "Skip running everest eightcells test on azure for now"
        return 0
    elif [[ "$CI_RUNNER_LABEL" == "onprem" ]]; then
        RUNNER_ROOT="/scratch/oompf/eightcells_tests"
    else
        echo "Unsupported runner label: $CI_RUNNER_LABEL"
        return 1
    fi

    mkdir -p "$RUNNER_ROOT"

    EIGHTCELLS_RUNPATH=$(mktemp -d -p "$RUNNER_ROOT")

    # Need to copy the eightcells test to a directory that is accessible by all cluster members
    cp -r "${CI_SOURCE_ROOT}/test-data/everest/eightcells" "$EIGHTCELLS_RUNPATH"
    chmod -R a+rx "$EIGHTCELLS_RUNPATH"
    pushd "${EIGHTCELLS_RUNPATH}/eightcells" || exit 1
    echo "EIGHTCELLS_RUNPATH: $EIGHTCELLS_RUNPATH"

    disable_komodo
    # shellcheck source=/dev/null
    source "${_KOMODO_ROOT}/${_FULL_RELEASE_NAME}/enable"

    CONFIG="everest/model/config.yml"
    if [[ "$CI_RUNNER_LABEL" == "azure" ]]; then
        sed -i "s/name: local/name: torque\n    queue: permanent_8/g" "$CONFIG"
        export PATH=$PATH:/opt/pbs/bin
    elif [[ "$CI_RUNNER_LABEL" == "onprem" ]]; then
        sed -i "s/name: local/name: lsf/g" "$CONFIG"
        export PATH=$PATH:/global/bin
    fi

    everest run "$CONFIG" --skip-prompt --debug --disable-monitoring
    STATUS=$?
    popd || exit 1

    if [ $STATUS -ne 0 ]; then
        echo "Everest eightcells test failed. Running everest kill"
        everest kill "$CONFIG"
    fi

    # Clean up the temp folder removing folders older than 7 days
    find "$RUNNER_ROOT" -maxdepth 1 -mtime +7 -user f_scout_ci -type d -exec rm -r {} \;

    return $STATUS
}

start_tests () {
    python -m pytest --test-resinsight
    run_everest_eightcells_test
}
