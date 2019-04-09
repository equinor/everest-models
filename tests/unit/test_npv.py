import argparse
import datetime
import os
import shutil
import sys

import pytest
from ecl.summary import EclSum

import yaml
from spinningjenny import npv_job
from spinningjenny.npv_job import _str2date
from spinningjenny.script import npv

_SUMMARY_FILE = "REEK-0.UNSMRY"
_CONFIG_FILE = "input_data.yml"
_TEST_DIR = os.path.join(os.path.dirname(
    os.path.dirname(__file__)), '../tests/testdata/npv/')


@pytest.fixture
def input_data(tmpdir):
    for file_name in os.listdir(_TEST_DIR):
        shutil.copy(_TEST_DIR + file_name, tmpdir.strpath)

    cwd = os.getcwd()
    tmpdir.chdir()

    with open('input_data.yml', 'r') as default_input_data:
        data = yaml.safe_load(default_input_data)

    yield data

    os.chdir(cwd)


@pytest.fixture
def options():
    sys.argv.extend(['--summary-file', _SUMMARY_FILE])
    sys.argv.extend(['--config-file', _CONFIG_FILE])

    return npv._extract_options(sys.argv)


def test_minimal_input_case_npv(tmpdir, input_data, options):
    input_data.pop('exchange_rates')
    input_data.pop('discount_rates')
    input_data.pop('costs')
    input_data.pop('well_costs')
    input_data.pop('summary_keys')
    input_data.pop('dates')

    npv._prepare_config(input_data, options)

    calculate = npv.CalculateNPV(input_data)
    calculate.run()
    calculate.write()

    expected_npv = 1361320463.83
    assert calculate.npv == expected_npv
    assert calculate.multiplier == 1
    assert sorted(calculate.keywords) == sorted(
        ['FOPT', 'FWPT', 'FGPT', 'FWIT', 'FGIT', 'GOPT:OP'])

    assert_written_npv(tmpdir, expected_npv, input_data)


def test_base_case_npv(tmpdir, input_data, options):
    input_data.pop('discount_rates')
    input_data.pop('costs')
    input_data.pop('summary_keys')
    input_data.pop('dates')

    npv._prepare_config(input_data, options)

    calculate = npv.CalculateNPV(input_data)
    calculate.run()
    calculate.write()

    expected_npv = 2746456461.88
    assert calculate.npv == expected_npv
    assert calculate.multiplier == 1
    assert sorted(calculate.keywords) == sorted(
        ['FOPT', 'FWPT', 'FGPT', 'FWIT', 'FGIT', 'GOPT:OP'])

    assert_written_npv(tmpdir, expected_npv, input_data)


def test_extended_case_npv(tmpdir, input_data, options):
    input_data.pop('dates')
    input_data.pop('summary_keys')

    npv._prepare_config(input_data, options)

    calculate = npv.CalculateNPV(input_data)
    calculate.run()
    calculate.write()

    expected_npv = 2787975581.67
    assert calculate.npv == expected_npv
    assert calculate.multiplier == 1
    assert sorted(calculate.keywords) == sorted(
        ['FOPT', 'FWPT', 'FGPT', 'FWIT', 'FGIT', 'GOPT:OP'])

    assert_written_npv(tmpdir, expected_npv, input_data)


def test_alter_mult(tmpdir, input_data, options):
    input_data.pop('dates')
    input_data.pop('summary_keys')
    multiplier = 2
    input_data['multiplier'] = multiplier

    npv._prepare_config(input_data, options)

    calculate = npv.CalculateNPV(input_data)
    calculate.run()
    calculate.write()

    expected_npv = multiplier * 2787975581.67
    assert calculate.npv == expected_npv
    assert calculate.multiplier == multiplier
    assert sorted(calculate.keywords) == sorted(
        ['FOPT', 'FWPT', 'FGPT', 'FWIT', 'FGIT', 'GOPT:OP'])

    assert_written_npv(tmpdir, expected_npv, input_data)


def test_extended_case_mutated_ref_date_npv(tmpdir, input_data, options):
    input_data['dates'].pop('start_date')
    input_data['dates'].pop('end_date')
    input_data['dates']['ref_date'] = '06.05.2000'
    input_data.pop('summary_keys')

    npv._prepare_config(input_data, options)

    calculate = npv.CalculateNPV(input_data)
    calculate.run()
    calculate.write()

    expected_npv = 2841341281.17
    assert calculate.npv == expected_npv
    assert sorted(calculate.keywords) == sorted(
        ['FOPT', 'FWPT', 'FGPT', 'FWIT', 'FGIT', 'GOPT:OP'])

    assert_written_npv(tmpdir, expected_npv, input_data)


def test_extended_case_date_mutated_npv(tmpdir, input_data, options):
    input_data['dates'].pop('ref_date')
    input_data['dates']['start_date'] = '12.06.2000'
    input_data['dates']['end_date'] = '23.12.2002'

    npv._prepare_config(input_data, options)

    calculate = npv.CalculateNPV(input_data)
    calculate.run()
    calculate.write()

    expected_npv = 882224967.83
    assert calculate.npv == expected_npv
    assert sorted(calculate.keywords) == sorted(['FWIT', 'FOPT'])

    assert_written_npv(tmpdir, expected_npv, input_data)


def test_extended_case_big_date_range_npv(tmpdir, input_data, options):
    input_data['dates'].pop('ref_date')
    input_data['dates']['start_date'] = '01.12.1999'
    input_data['dates']['end_date'] = '01.01.2003'
    input_data.pop('summary_keys')

    npv._prepare_config(input_data, options)

    calculate = npv.CalculateNPV(input_data)
    calculate.run()
    calculate.write()

    expected_npv = 2787975581.67
    assert calculate.npv == expected_npv
    assert sorted(calculate.keywords) == sorted(
        ['FOPT', 'FWPT', 'FGPT', 'FWIT', 'FGIT', 'GOPT:OP'])

    assert_written_npv(tmpdir, expected_npv, input_data)


def test_extended_case_small_date_range_npv(tmpdir, input_data, options):
    input_data['dates'].pop('ref_date')
    input_data['dates']['start_date'] = '01.12.1999'
    input_data['dates']['end_date'] = '02.12.1999'
    input_data.pop('summary_keys')

    npv._prepare_config(input_data, options)

    calculate = npv.CalculateNPV(input_data)
    calculate.run()
    calculate.write()

    expected_npv = -370456890.60
    assert calculate.npv == expected_npv
    assert sorted(calculate.keywords) == sorted(
        ['FOPT', 'FWPT', 'FGPT', 'FWIT', 'FGIT', 'GOPT:OP'])

    assert_written_npv(tmpdir, expected_npv, input_data)


def test_dates_outside_simulation_dates(tmpdir, input_data, options):
    input_data['dates'].pop('ref_date')
    input_data['dates']['start_date'] = '30.11.1998'
    input_data['dates']['end_date'] = '02.01.2005'

    npv._prepare_config(input_data, options)

    calculate_outside_sim_dates = npv.CalculateNPV(input_data)
    calculate_outside_sim_dates.run()
    outside_sim_dates_npv = calculate_outside_sim_dates.npv

    input_data.pop('dates')

    npv._prepare_config(input_data, options)

    calculate_inside_sim_dates = npv.CalculateNPV(input_data)
    calculate_inside_sim_dates.run()
    default_sim_dates_npv = calculate_inside_sim_dates.npv

    assert outside_sim_dates_npv == default_sim_dates_npv


def test_missing_price_info(tmpdir, input_data, options):
    input_data.pop('prices')

    npv._prepare_config(input_data, options)

    with pytest.raises(AttributeError) as excinfo:
        npv.CalculateNPV(input_data)

    assert 'Price information is required to do an NPV calculation' in str(
        excinfo.value)


def test_keys_not_available(tmpdir, input_data, options):
    input_data['summary_keys'] = ["NOT_EXISTING", "FAULTY_KEY"]

    npv._prepare_config(input_data, options)

    with pytest.raises(AttributeError) as excinfo:
        calculate = npv.CalculateNPV(input_data)
        calculate.keywords

    assert "Missing required data (['NOT_EXISTING', 'FAULTY_KEY']) in summary file." in str(
        excinfo.value)


def test_no_date_input(tmpdir, input_data, options):
    input_data.pop('dates')

    npv._prepare_config(input_data, options)

    calculate = npv.CalculateNPV(input_data)
    calculate.run()

    assert calculate.date_handler.start_date == calculate.ecl_sum.start_time
    assert calculate.date_handler.end_date == calculate.ecl_sum.end_time
    assert calculate.date_handler.ref_date == calculate.ecl_sum.start_time


def test_date_input(tmpdir, input_data, options):
    _start_date = '01.02.2000'
    _end_date = '01.01.2001'
    _ref_date = '02.02.2000'
    input_data['dates']['start_date'] = _start_date
    input_data['dates']['end_date'] = _end_date
    input_data['dates']['ref_date'] = _ref_date

    npv._prepare_config(input_data, options)

    calculate = npv.CalculateNPV(input_data)
    calculate.run()

    assert calculate.date_handler.start_date == _str2date(_start_date)
    assert calculate.date_handler.end_date == _str2date(_end_date)
    assert calculate.date_handler.ref_date == _str2date(_ref_date)


def test_start_date_after_end_date(tmpdir, input_data, options):
    _start_date = '01.02.2001'
    _end_date = '01.01.2001'
    input_data['dates']['start_date'] = _start_date
    input_data['dates']['end_date'] = _end_date

    npv._prepare_config(input_data, options)

    with pytest.raises(ValueError) as excinfo:
        npv.CalculateNPV(input_data)

    assert "Invalid time interval start after end" in str(
        excinfo.value)


def test_find_discount_value_lower_extreme(tmpdir, input_data):
    date = datetime.datetime(1900, 1, 1)
    discount_rate = npv_job.DiscountRate(input_data)
    assert discount_rate.get(date) == discount_rate.default_discount_rate


def test_find_discount_value_lower_limit(tmpdir, input_data):
    date = datetime.datetime(1999, 1, 1)
    discount_rate = npv_job.DiscountRate(input_data)
    assert discount_rate.get(date) == 0.02


def test_find_discount_value_base_case(tmpdir, input_data):
    date = datetime.datetime(2001, 2, 1)
    discount_rate = npv_job.DiscountRate(input_data)
    assert discount_rate.get(date) == 0.02


def test_find_discount_value_upper_limit(tmpdir, input_data):
    date = datetime.datetime(2002, 1, 1)
    discount_rate = npv_job.DiscountRate(input_data)
    assert discount_rate.get(date) == 0.05


def test_find_discount_value_upper_extreme(tmpdir, input_data):
    date = datetime.datetime(2010, 1, 1)
    discount_rate = npv_job.DiscountRate(input_data)
    assert discount_rate.get(date) == 0.05


def test_find_exhange_rate_lower_extreme(tmpdir, input_data):
    date = datetime.datetime(1990, 1, 1)
    currency = 'USD'
    exchange_rate = npv_job.ExchangeRate(input_data)
    assert exchange_rate.get(date, currency) == 1.0


def test_find_exhange_rate_lower_limit(tmpdir, input_data):
    date = datetime.datetime(1997, 1, 1)
    currency = 'USD'
    exchange_rate = npv_job.ExchangeRate(input_data)
    assert exchange_rate.get(date, currency) == 5.0


def test_find_exhange_rate_base_case(tmpdir, input_data):
    date = datetime.datetime(1999, 12, 2)
    currency = 'USD'
    exchange_rate = npv_job.ExchangeRate(input_data)
    assert exchange_rate.get(date, currency) == 5.0


def test_find_exhange_rate_upper_limit(tmpdir, input_data):
    date = datetime.datetime(2002, 2, 1)
    currency = 'USD'
    exchange_rate = npv_job.ExchangeRate(input_data)
    assert exchange_rate.get(date, currency) == 9.0


def test_find_exhange_rate_upper_extreme(tmpdir, input_data):
    date = datetime.datetime(2010, 1, 1)
    currency = 'USD'
    exchange_rate = npv_job.ExchangeRate(input_data)
    assert exchange_rate.get(date, currency) == 9.0


def test_find_price_lower_extreme(tmpdir, input_data):
    date = datetime.datetime(1990, 1, 1)
    keyword = 'FWPT'
    price = npv_job.Price(input_data)
    exchange_rate = npv_job.ExchangeRate(input_data)
    transaction = price.get(date, keyword)
    assert transaction.currency == None
    assert transaction._value == 0
    assert transaction.value(exchange_rate) == 0


def test_find_price_lower_limit(tmpdir, input_data):
    date = datetime.datetime(1999, 1, 1)
    keyword = 'FWPT'
    price = npv_job.Price(input_data)
    exchange_rate = npv_job.ExchangeRate(input_data)
    transaction = price.get(date, keyword)
    assert transaction.currency == 'USD'
    assert transaction._value == -5
    assert transaction.value(exchange_rate) == -25


def test_find_price_base_case(tmpdir, input_data):
    date = datetime.datetime(1999, 12, 2)
    keyword = 'FWPT'
    price = npv_job.Price(input_data)
    exchange_rate = npv_job.ExchangeRate(input_data)
    transaction = price.get(date, keyword)
    assert transaction.currency == 'USD'
    assert transaction.value(exchange_rate) == -25


def test_find_price_upper_limit(tmpdir, input_data):
    date = datetime.datetime(2002, 2, 1)
    keyword = 'FWPT'
    price = npv_job.Price(input_data)
    exchange_rate = npv_job.ExchangeRate(input_data)
    transaction = price.get(date, keyword)
    assert transaction.currency == None
    assert transaction._value == -2
    assert transaction.value(exchange_rate) == -2


def test_find_price_upper_extreme(tmpdir, input_data):
    date = datetime.datetime(2010, 1, 1)
    keyword = 'FWPT'
    price = npv_job.Price(input_data)
    exchange_rate = npv_job.ExchangeRate(input_data)
    transaction = price.get(date, keyword)
    assert transaction.currency == None
    assert transaction._value == -2
    assert transaction.value(exchange_rate) == -2


def test_find_price_keyword_not_exists(tmpdir, input_data):
    date = datetime.datetime(2010, 1, 1)
    keyword = 'NOT_A_KEY'
    with pytest.raises(AttributeError) as excinfo:
        price = npv_job.Price(input_data)
        price.get(date, keyword)

    assert 'Price information missing for NOT_A_KEY' in str(excinfo.value)

def assert_written_npv(tmpdir, expected_npv, input_data):
    written_npv_output_file = tmpdir.strpath + "/" + \
        input_data.get('files').get('output_file')
    assert os.path.isfile(written_npv_output_file)
    with open(written_npv_output_file, 'r') as written_npv_output:
        assert float(written_npv_output.readline()) == expected_npv
