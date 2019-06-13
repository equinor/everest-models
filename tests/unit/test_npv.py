import argparse
import datetime
import os
import shutil
import sys

import pytest
import yaml
from ecl.summary import EclSum

import spinningjenny
from spinningjenny.npv import npv_config, npv_job
from spinningjenny.script import npv

_SUMMARY_FILE = "REEK-0.UNSMRY"
_CONFIG_FILE = "input_data.yml"
_TEST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "../tests/testdata/npv/"
)


@pytest.fixture
def input_data(tmpdir):
    for file_name in os.listdir(_TEST_DIR):
        shutil.copy(_TEST_DIR + file_name, tmpdir.strpath)

    cwd = os.getcwd()
    tmpdir.chdir()

    with open("input_data.yml", "r") as default_input_data:
        data = yaml.safe_load(default_input_data)

    yield data

    os.chdir(cwd)


@pytest.fixture
def options():
    sys.argv.extend(["--summary-file", _SUMMARY_FILE])
    sys.argv.extend(["--config-file", _CONFIG_FILE])

    return npv._extract_options(sys.argv)


def test_minimal_input_case_npv(tmpdir, input_data, options):
    input_data.pop("exchange_rates")
    input_data.pop("discount_rates")
    input_data.pop("costs")
    input_data.pop("well_costs")
    input_data.pop("summary_keys")
    input_data.pop("dates")

    config = npv._prepare_config(input_data, options)
    assert config.valid

    calculate = npv.CalculateNPV(config.snapshot, options.summary_file)
    calculate.run()
    calculate.write()

    expected_npv = 1361320463.83
    assert calculate.npv == expected_npv
    assert calculate.multiplier == 1
    assert sorted(calculate.keywords) == sorted(
        ["FOPT", "FWPT", "FGPT", "FWIT", "FGIT", "GOPT:OP"]
    )

    assert_written_npv(tmpdir, expected_npv, config.snapshot)


def test_base_case_npv(tmpdir, input_data, options):
    input_data.pop("discount_rates")
    input_data.pop("costs")
    input_data.pop("summary_keys")
    input_data.pop("dates")

    config = npv._prepare_config(input_data, options)
    assert config.valid

    calculate = npv.CalculateNPV(config.snapshot, options.summary_file)
    calculate.run()
    calculate.write()

    expected_npv = 2746456461.88
    assert calculate.npv == expected_npv
    assert calculate.multiplier == 1
    assert sorted(calculate.keywords) == sorted(
        ["FOPT", "FWPT", "FGPT", "FWIT", "FGIT", "GOPT:OP"]
    )

    assert_written_npv(tmpdir, expected_npv, config.snapshot)


def test_extended_case_npv(tmpdir, input_data, options):
    input_data.pop("dates")
    input_data.pop("summary_keys")

    config = npv._prepare_config(input_data, options)
    assert config.valid

    calculate = npv.CalculateNPV(config.snapshot, options.summary_file)
    calculate.run()
    calculate.write()

    expected_npv = 2787975581.67
    assert calculate.npv == expected_npv
    assert calculate.multiplier == 1
    assert sorted(calculate.keywords) == sorted(
        ["FOPT", "FWPT", "FGPT", "FWIT", "FGIT", "GOPT:OP"]
    )

    assert_written_npv(tmpdir, expected_npv, config.snapshot)


def test_alter_mult(tmpdir, input_data, options):
    input_data.pop("dates")
    input_data.pop("summary_keys")
    multiplier = 2
    input_data["multiplier"] = multiplier

    config = npv._prepare_config(input_data, options)
    assert config.valid

    calculate = npv.CalculateNPV(config.snapshot, options.summary_file)
    calculate.run()
    calculate.write()

    expected_npv = multiplier * 2787975581.67
    assert calculate.npv == expected_npv
    assert calculate.multiplier == multiplier
    assert sorted(calculate.keywords) == sorted(
        ["FOPT", "FWPT", "FGPT", "FWIT", "FGIT", "GOPT:OP"]
    )

    assert_written_npv(tmpdir, expected_npv, config.snapshot)


def test_extended_case_mutated_ref_date_npv(tmpdir, input_data, options):
    input_data["dates"].pop("start_date")
    input_data["dates"].pop("end_date")
    input_data["dates"]["ref_date"] = datetime.date(2000, 5, 6)
    input_data.pop("summary_keys")

    config = npv._prepare_config(input_data, options)
    assert config.valid

    calculate = npv.CalculateNPV(config.snapshot, options.summary_file)
    calculate.run()
    calculate.write()

    expected_npv = 2841341281.17
    assert calculate.npv == expected_npv
    assert sorted(calculate.keywords) == sorted(
        ["FOPT", "FWPT", "FGPT", "FWIT", "FGIT", "GOPT:OP"]
    )

    assert_written_npv(tmpdir, expected_npv, config.snapshot)


def test_extended_case_date_mutated_npv(tmpdir, input_data, options):
    input_data["dates"].pop("ref_date")
    input_data["dates"]["start_date"] = datetime.date(2000, 6, 12)
    input_data["dates"]["end_date"] = datetime.date(2002, 12, 23)

    config = npv._prepare_config(input_data, options)
    assert config.valid

    calculate = npv.CalculateNPV(config.snapshot, options.summary_file)
    calculate.run()
    calculate.write()

    expected_npv = 908267869.83
    assert calculate.npv == expected_npv
    assert sorted(calculate.keywords) == sorted(["FWIT", "FOPT"])

    assert_written_npv(tmpdir, expected_npv, config.snapshot)


def test_extended_case_big_date_range_npv(tmpdir, input_data, options):
    input_data["dates"].pop("ref_date")
    input_data["dates"]["start_date"] = datetime.date(1999, 12, 1)
    input_data["dates"]["end_date"] = datetime.date(2003, 1, 1)
    input_data.pop("summary_keys")

    config = npv._prepare_config(input_data, options)
    assert config.valid

    calculate = npv.CalculateNPV(config.snapshot, options.summary_file)
    calculate.run()
    calculate.write()

    expected_npv = 2787975581.67
    assert calculate.npv == expected_npv
    assert sorted(calculate.keywords) == sorted(
        ["FOPT", "FWPT", "FGPT", "FWIT", "FGIT", "GOPT:OP"]
    )

    assert_written_npv(tmpdir, expected_npv, config.snapshot)


def test_extended_case_small_date_range_npv(tmpdir, input_data, options):
    input_data["dates"].pop("ref_date")
    input_data["dates"]["start_date"] = datetime.date(1999, 12, 1)
    input_data["dates"]["end_date"] = datetime.date(1999, 12, 2)
    input_data.pop("summary_keys")

    config = npv._prepare_config(input_data, options)
    assert config.valid

    calculate = npv.CalculateNPV(config.snapshot, options.summary_file)
    calculate.run()
    calculate.write()

    expected_npv = -370456890.60
    assert calculate.npv == expected_npv
    assert sorted(calculate.keywords) == sorted(
        ["FOPT", "FWPT", "FGPT", "FWIT", "FGIT", "GOPT:OP"]
    )

    assert_written_npv(tmpdir, expected_npv, config.snapshot)


def test_dates_outside_simulation_dates(tmpdir, input_data, options):
    input_data["dates"].pop("ref_date")
    input_data["dates"]["start_date"] = datetime.date(1998, 11, 30)
    input_data["dates"]["end_date"] = datetime.date(2005, 1, 2)

    config = npv._prepare_config(input_data, options)
    assert config.valid

    calculate_outside_sim_dates = npv.CalculateNPV(
        config.snapshot, options.summary_file
    )
    calculate_outside_sim_dates.run()
    outside_sim_dates_npv = calculate_outside_sim_dates.npv

    input_data.pop("dates")

    config = npv._prepare_config(input_data, options)

    calculate_inside_sim_dates = npv.CalculateNPV(config.snapshot, options.summary_file)
    calculate_inside_sim_dates.run()
    default_sim_dates_npv = calculate_inside_sim_dates.npv

    assert outside_sim_dates_npv == default_sim_dates_npv


def test_keys_not_available(tmpdir, input_data, options):
    input_data["summary_keys"] = ["NOT_EXISTING", "FAULTY_KEY"]

    config = npv._prepare_config(input_data, options)

    with pytest.raises(AttributeError) as excinfo:
        calculate = npv.CalculateNPV(config.snapshot, options.summary_file)
        calculate.keywords

    assert (
        "Missing required data (['NOT_EXISTING', 'FAULTY_KEY']) in summary file."
        in str(excinfo.value)
    )


def test_no_date_input(tmpdir, input_data, options):
    input_data.pop("dates")

    config = npv._prepare_config(input_data, options)
    assert config.valid

    calculate = npv.CalculateNPV(config.snapshot, options.summary_file)

    assert calculate.date_handler.start_date == calculate.ecl_sum.start_date
    assert calculate.date_handler.end_date == calculate.ecl_sum.end_date
    assert calculate.date_handler.ref_date == calculate.ecl_sum.start_date


def test_date_input(tmpdir, input_data, options):
    _start_date = datetime.date(2000, 2, 1)
    _end_date = datetime.date(2001, 1, 1)
    _ref_date = datetime.date(2000, 2, 2)
    input_data["dates"]["start_date"] = _start_date
    input_data["dates"]["end_date"] = _end_date
    input_data["dates"]["ref_date"] = _ref_date

    config = npv._prepare_config(input_data, options)
    assert config.valid

    calculate = npv.CalculateNPV(config.snapshot, options.summary_file)

    assert calculate.date_handler.start_date == _start_date
    assert calculate.date_handler.end_date == _end_date
    assert calculate.date_handler.ref_date == _ref_date


def test_start_date_after_end_date(tmpdir, input_data, options):
    _start_date = datetime.date(2001, 2, 1)
    _end_date = datetime.date(2001, 1, 1)
    input_data["dates"]["start_date"] = _start_date
    input_data["dates"]["end_date"] = _end_date

    config = npv._prepare_config(input_data, options)
    assert config.valid

    with pytest.raises(ValueError) as excinfo:
        npv.CalculateNPV(config.snapshot, options.summary_file)

    assert "Invalid time interval start after end" in str(excinfo.value)


def test_find_discount_value_lower_extreme(tmpdir, input_data, options):
    date = datetime.date(1900, 1, 1)

    config = npv._prepare_config(input_data, options)
    assert config.valid

    discount_rate = npv_job.DiscountRate(config.snapshot)
    assert discount_rate.get(date) == discount_rate.default_discount_rate


def test_find_discount_value_lower_limit(tmpdir, input_data, options):
    date = datetime.date(1999, 1, 1)

    config = npv._prepare_config(input_data, options)
    assert config.valid

    discount_rate = npv_job.DiscountRate(config.snapshot)
    assert discount_rate.get(date) == 0.02


def test_find_discount_value_base_case(tmpdir, input_data, options):
    date = datetime.date(2001, 2, 1)

    config = npv._prepare_config(input_data, options)
    assert config.valid

    discount_rate = npv_job.DiscountRate(config.snapshot)
    assert discount_rate.get(date) == 0.02


def test_find_discount_value_upper_limit(tmpdir, input_data, options):
    date = datetime.date(2002, 1, 1)

    config = npv._prepare_config(input_data, options)
    assert config.valid

    discount_rate = npv_job.DiscountRate(config.snapshot)
    assert discount_rate.get(date) == 0.05


def test_find_discount_value_upper_extreme(tmpdir, input_data, options):
    date = datetime.date(2010, 1, 1)

    config = npv._prepare_config(input_data, options)
    assert config.valid

    discount_rate = npv_job.DiscountRate(config.snapshot)
    assert discount_rate.get(date) == 0.05


def test_find_exhange_rate_lower_extreme(tmpdir, input_data, options):
    date = datetime.date(1990, 1, 1)
    currency = "USD"

    config = npv._prepare_config(input_data, options)
    assert config.valid

    exchange_rate = npv_job.ExchangeRate(config.snapshot)
    assert exchange_rate.get(date, currency) == 1.0


def test_find_exhange_rate_lower_limit(tmpdir, input_data, options):
    date = datetime.date(1997, 1, 1)
    currency = "USD"

    config = npv._prepare_config(input_data, options)
    assert config.valid

    exchange_rate = npv_job.ExchangeRate(config.snapshot)
    assert exchange_rate.get(date, currency) == 5.0


def test_find_exhange_rate_base_case(tmpdir, input_data, options):
    date = datetime.date(1999, 12, 2)
    currency = "USD"

    config = npv._prepare_config(input_data, options)
    assert config.valid

    exchange_rate = npv_job.ExchangeRate(config.snapshot)
    assert exchange_rate.get(date, currency) == 5.0


def test_find_exhange_rate_upper_limit(tmpdir, input_data, options):
    date = datetime.date(2002, 2, 1)
    currency = "USD"

    config = npv._prepare_config(input_data, options)
    assert config.valid

    exchange_rate = npv_job.ExchangeRate(config.snapshot)
    assert exchange_rate.get(date, currency) == 9.0


def test_find_exhange_rate_upper_extreme(tmpdir, input_data, options):
    date = datetime.date(2010, 1, 1)
    currency = "USD"

    config = npv._prepare_config(input_data, options)
    exchange_rate = npv_job.ExchangeRate(config.snapshot)
    assert exchange_rate.get(date, currency) == 9.0


def test_find_price_lower_extreme(tmpdir, input_data, options):
    date = datetime.date(1990, 1, 1)
    keyword = "FWPT"

    config = npv._prepare_config(input_data, options)
    assert config.valid

    price = npv_job.Price(config.snapshot)
    exchange_rate = npv_job.ExchangeRate(config.snapshot)
    transaction = price.get(date, keyword)
    assert transaction.currency == None
    assert transaction._value == 0
    assert transaction.value(exchange_rate) == 0


def test_find_price_lower_limit(tmpdir, input_data, options):
    date = datetime.date(1999, 1, 1)
    keyword = "FWPT"

    config = npv._prepare_config(input_data, options)
    assert config.valid

    price = npv_job.Price(config.snapshot)
    exchange_rate = npv_job.ExchangeRate(config.snapshot)
    transaction = price.get(date, keyword)
    assert transaction.currency == "USD"
    assert transaction._value == -5
    assert transaction.value(exchange_rate) == -25


def test_find_price_base_case(tmpdir, input_data, options):
    date = datetime.date(1999, 12, 2)
    keyword = "FWPT"

    config = npv._prepare_config(input_data, options)
    assert config.valid

    price = npv_job.Price(config.snapshot)
    exchange_rate = npv_job.ExchangeRate(config.snapshot)
    transaction = price.get(date, keyword)
    assert transaction.currency == "USD"
    assert transaction.value(exchange_rate) == -25


def test_find_price_upper_limit(tmpdir, input_data, options):
    date = datetime.date(2002, 2, 1)
    keyword = "FWPT"

    config = npv._prepare_config(input_data, options)
    assert config.valid

    price = npv_job.Price(config.snapshot)
    exchange_rate = npv_job.ExchangeRate(config.snapshot)
    transaction = price.get(date, keyword)
    assert transaction.currency == None
    assert transaction._value == -2
    assert transaction.value(exchange_rate) == -2


def test_find_price_upper_extreme(tmpdir, input_data, options):
    date = datetime.date(2010, 1, 1)
    keyword = "FWPT"

    config = npv._prepare_config(input_data, options)
    assert config.valid

    price = npv_job.Price(config.snapshot)
    exchange_rate = npv_job.ExchangeRate(config.snapshot)
    transaction = price.get(date, keyword)
    assert transaction.currency == None
    assert transaction._value == -2
    assert transaction.value(exchange_rate) == -2


def test_find_price_keyword_not_exists(tmpdir, input_data, options):
    date = datetime.date(2010, 1, 1)
    keyword = "NOT_A_KEY"

    config = npv._prepare_config(input_data, options)
    assert config.valid

    price = npv_job.Price(config.snapshot)
    with pytest.raises(AttributeError) as excinfo:
        price.get(date, keyword)

    assert "Price information missing for NOT_A_KEY" in str(excinfo.value)


def test_argparser(tmpdir, input_data):
    output_file = "test"
    input_file = "wells.json"
    start_date = datetime.date(2018, 1, 31)
    end_date = datetime.date(2019, 6, 22)
    ref_date = datetime.date(2018, 4, 5)
    default_discount_rate = 2
    default_exchange_rate = 5.0
    multiplier = 2

    sys.argv.extend(["--summary-file", _SUMMARY_FILE])
    sys.argv.extend(["--config-file", _CONFIG_FILE])
    sys.argv.extend(["--output-file", output_file])
    sys.argv.extend(["--input-file", input_file])
    sys.argv.extend(["--start-date", str(start_date)])
    sys.argv.extend(["--end-date", str(end_date)])
    sys.argv.extend(["--ref-date", str(ref_date)])
    sys.argv.extend(["--default-discount-rate", str(default_discount_rate)])
    sys.argv.extend(["--default-exchange-rate", str(default_exchange_rate)])
    sys.argv.extend(["--multiplier", str(multiplier)])

    options = spinningjenny.script.npv._extract_options(sys.argv)
    config = spinningjenny.script.npv._prepare_config(input_data, options)

    assert config.snapshot.files.output_file == output_file
    assert config.snapshot.files.input_file == input_file
    assert config.snapshot.dates.start_date == start_date
    assert config.snapshot.dates.end_date == end_date
    assert config.snapshot.dates.ref_date == ref_date
    assert config.snapshot.default_discount_rate == default_discount_rate
    assert config.snapshot.default_exchange_rate == default_exchange_rate
    assert config.snapshot.multiplier == multiplier


def assert_written_npv(tmpdir, expected_npv, input_data):
    written_npv_output_file = tmpdir.strpath + "/" + input_data.files.output_file
    assert os.path.isfile(written_npv_output_file)
    with open(written_npv_output_file, "r") as written_npv_output:
        assert float(written_npv_output.readline()) == expected_npv
