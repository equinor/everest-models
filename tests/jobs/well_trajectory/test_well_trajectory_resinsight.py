import logging

import pytest
from everest_models.jobs.fm_well_trajectory.well_trajectory_resinsight import ResInsight


@pytest.mark.resinsight
def test_failing_start_resinsight(caplog):
    caplog.set_level(logging.INFO)
    with pytest.raises(ConnectionError):
        with ResInsight("_non_existing_binary_"):
            pass
    assert "Launching ResInsight..." in caplog.text


@pytest.mark.resinsight
def test_start_resinsight():
    with ResInsight() as ri:
        assert ri.project.cases() == []
