import datetime
import os

import pytest
from jobs.npv.helper import _CONFIG_FILE, assert_written_npv

from jobs.fm_npv import cli, tasks

_INPUT_FILE_ONE_WELL = "one_well.json"


def test_default_options_valid_config(default_options):
    config = cli._prepare_config(default_options)
    assert config.valid


def test_base_case_npv(tmpdir, default_options):
    config = cli._prepare_config(default_options)

    calculate = cli.CalculateNPV(config.snapshot, default_options.summary)
    calculate.run()
    calculate.write()

    expected_npv = 691981114.68
    assert calculate.npv == expected_npv
    assert calculate.multiplier == 1
    assert sorted(calculate.keywords) == sorted(["FOPT", "FWIT"])

    assert_written_npv(tmpdir, expected_npv, config.snapshot.files.output_file)


def test_base_case_npv_no_input(tmpdir, default_options):
    well_cost = 1000000
    readydate = datetime.date.fromisoformat("2000-06-14")
    discount_rate = 0.02
    default_options.input = _INPUT_FILE_ONE_WELL
    config = cli._prepare_config(default_options)

    calculate = cli.CalculateNPV(config.snapshot, default_options.summary)
    calculate.run()
    calculate.write()
    npv_output_file = os.path.join(tmpdir.strpath, config.snapshot.files.output_file)

    assert os.path.isfile(npv_output_file)
    with open(npv_output_file, "r") as npv_output:
        npv_with_well = float(npv_output.readline())

    expected_well_cost = well_cost / (1.0 + discount_rate) ** (
        (readydate - config.snapshot.dates.ref_date).days / 365.25
    )

    default_options.input = None
    config = cli._prepare_config(default_options)

    calculate = cli.CalculateNPV(config.snapshot, default_options.summary)
    calculate.run()
    calculate.write()

    allowed_error = 0.01
    expected_npv_without_well = npv_with_well + expected_well_cost
    assert abs(calculate.npv - expected_npv_without_well) <= allowed_error
    assert calculate.multiplier == 1
    assert sorted(calculate.keywords) == sorted(["FOPT", "FWIT"])


def test_extended_case_npv(tmpdir, default_options):
    config = cli._prepare_config(default_options)

    snapshot = config.snapshot._replace(dates=None, summary_keys=None)
    calculate = cli.CalculateNPV(snapshot, default_options.summary)
    calculate.run()
    calculate.write()

    expected_npv = 1323951495.03
    assert calculate.npv == expected_npv
    assert calculate.multiplier == 1
    assert sorted(calculate.keywords) == sorted(
        ["FOPT", "FWPT", "FGPT", "FWIT", "FGIT", "GOPT:OP"]
    )

    assert_written_npv(tmpdir, expected_npv, config.snapshot.files.output_file)


def test_alter_mult(tmpdir, default_options):
    multiplier = 2
    config = cli._prepare_config(default_options)

    snapshot = config.snapshot._replace(
        dates=None, summary_keys=None, multiplier=multiplier
    )
    calculate = cli.CalculateNPV(snapshot, default_options.summary)
    calculate.run()
    calculate.write()

    expected_npv = 2647902990.07
    assert calculate.npv == expected_npv
    assert calculate.multiplier == multiplier
    assert sorted(calculate.keywords) == sorted(
        ["FOPT", "FWPT", "FGPT", "FWIT", "FGIT", "GOPT:OP"]
    )

    assert_written_npv(tmpdir, expected_npv, config.snapshot.files.output_file)


def test_extended_case_mutated_ref_date_npv(tmpdir, default_options):
    config = cli._prepare_config(default_options)

    snapshot = config.snapshot._replace(
        dates=config.snapshot.dates._replace(
            start_date=None, end_date=None, ref_date=datetime.date(2000, 5, 6)
        ),
        summary_keys=None,
    )

    calculate = cli.CalculateNPV(snapshot, default_options.summary)
    calculate.run()
    calculate.write()

    expected_npv = 1344403927.71
    assert calculate.npv == expected_npv
    assert sorted(calculate.keywords) == sorted(
        ["FOPT", "FWPT", "FGPT", "FWIT", "FGIT", "GOPT:OP"]
    )

    assert_written_npv(tmpdir, expected_npv, config.snapshot.files.output_file)


def test_extended_case_date_mutated_npv(tmpdir, default_options):

    config = cli._prepare_config(default_options)

    snapshot = config.snapshot._replace(
        dates=config.snapshot.dates._replace(
            start_date=datetime.date(2000, 6, 12),
            end_date=datetime.date(2002, 12, 23),
            ref_date=None,
        )
    )

    calculate = cli.CalculateNPV(snapshot, default_options.summary)
    calculate.run()
    calculate.write()

    expected_npv = 923994410.31
    assert calculate.npv == expected_npv
    assert sorted(calculate.keywords) == sorted(["FWIT", "FOPT"])

    assert_written_npv(tmpdir, expected_npv, config.snapshot.files.output_file)


def test_extended_case_big_date_range_npv(tmpdir, default_options):
    config = cli._prepare_config(default_options)

    snapshot = config.snapshot._replace(
        dates=config.snapshot.dates._replace(
            start_date=datetime.date(1999, 12, 1),
            end_date=datetime.date(2003, 1, 1),
            ref_date=None,
        ),
        summary_keys=None,
    )

    calculate = cli.CalculateNPV(snapshot, default_options.summary)
    calculate.run()
    calculate.write()

    expected_npv = 1165564342.7
    assert calculate.npv == expected_npv
    assert sorted(calculate.keywords) == sorted(
        ["FOPT", "FWPT", "FGPT", "FWIT", "FGIT", "GOPT:OP"]
    )

    assert_written_npv(tmpdir, expected_npv, config.snapshot.files.output_file)


def test_extended_case_small_date_range_npv(tmpdir, default_options):
    config = cli._prepare_config(default_options)

    snapshot = config.snapshot._replace(
        dates=config.snapshot.dates._replace(
            start_date=datetime.date(1999, 12, 1),
            end_date=datetime.date(1999, 12, 2),
            ref_date=None,
        ),
        summary_keys=None,
    )

    calculate = cli.CalculateNPV(snapshot, default_options.summary)
    calculate.run()
    calculate.write()

    expected_npv = -369456947.15
    assert calculate.npv == expected_npv
    assert sorted(calculate.keywords) == sorted(
        ["FOPT", "FWPT", "FGPT", "FWIT", "FGIT", "GOPT:OP"]
    )

    assert_written_npv(tmpdir, expected_npv, config.snapshot.files.output_file)


def test_dates_outside_simulation_dates(default_options):
    config = cli._prepare_config(default_options)

    snapshot = config.snapshot._replace(
        dates=config.snapshot.dates._replace(
            start_date=datetime.date(1998, 11, 30),
            end_date=datetime.date(2005, 1, 2),
            ref_date=None,
        )
    )

    calculate_outside_sim_dates = cli.CalculateNPV(snapshot, default_options.summary)
    calculate_outside_sim_dates.run()
    outside_sim_dates_npv = calculate_outside_sim_dates.npv

    snapshot = config.snapshot._replace(dates=None)

    calculate_inside_sim_dates = cli.CalculateNPV(snapshot, default_options.summary)
    calculate_inside_sim_dates.run()
    default_sim_dates_npv = calculate_inside_sim_dates.npv

    assert outside_sim_dates_npv == default_sim_dates_npv


def test_keys_not_available(default_options):
    config = cli._prepare_config(default_options)

    snapshot = config.snapshot._replace(summary_keys=["NOT_EXISTING", "FAULTY_KEY"])

    with pytest.raises(AttributeError) as excinfo:
        cli.CalculateNPV(snapshot, default_options.summary)

    assert (
        "Missing required data (['NOT_EXISTING', 'FAULTY_KEY']) in summary file."
        in str(excinfo.value)
    )


def test_no_date_input(default_options):
    config = cli._prepare_config(default_options)

    snapshot = config.snapshot._replace(dates=None)

    calculate = cli.CalculateNPV(snapshot, default_options.summary)

    assert calculate.date_handler.start_date == calculate.ecl_sum.start_date
    assert calculate.date_handler.end_date == calculate.ecl_sum.end_date
    assert calculate.date_handler.ref_date == calculate.ecl_sum.start_date


def test_date_input(default_options):
    _start_date = datetime.date(2000, 2, 1)
    _end_date = datetime.date(2001, 1, 1)
    _ref_date = datetime.date(2000, 2, 2)

    config = cli._prepare_config(default_options)

    snapshot = config.snapshot._replace(
        dates=config.snapshot.dates._replace(
            start_date=_start_date, end_date=_end_date, ref_date=_ref_date
        )
    )

    calculate = cli.CalculateNPV(snapshot, default_options.summary)

    assert calculate.date_handler.start_date == _start_date
    assert calculate.date_handler.end_date == _end_date
    assert calculate.date_handler.ref_date == _ref_date


def test_start_date_after_end_date(default_options):
    _start_date = datetime.date(2001, 2, 1)
    _end_date = datetime.date(2001, 1, 1)

    config = cli._prepare_config(default_options)

    snapshot = config.snapshot._replace(
        dates=config.snapshot.dates._replace(start_date=_start_date, end_date=_end_date)
    )

    with pytest.raises(ValueError) as excinfo:
        cli.CalculateNPV(snapshot, default_options.summary)

    assert "Invalid time interval start after end" in str(excinfo.value)


def test_find_discount_value_lower_extreme(default_options):
    date = datetime.date(1900, 1, 1)

    config = cli._prepare_config(default_options)

    discount_rate = tasks.DiscountRate(config.snapshot)
    assert discount_rate.get(date) == discount_rate.default_discount_rate


def test_find_discount_value_lower_limit(default_options):
    date = datetime.date(1999, 1, 1)

    config = cli._prepare_config(default_options)

    discount_rate = tasks.DiscountRate(config.snapshot)
    assert discount_rate.get(date) == 0.02


def test_find_discount_value_base_case(default_options):
    date = datetime.date(2001, 2, 1)

    config = cli._prepare_config(default_options)

    discount_rate = tasks.DiscountRate(config.snapshot)
    assert discount_rate.get(date) == 0.02


def test_find_discount_value_upper_limit(default_options):
    date = datetime.date(2002, 1, 1)

    config = cli._prepare_config(default_options)

    discount_rate = tasks.DiscountRate(config.snapshot)
    assert discount_rate.get(date) == 0.05


def test_find_discount_value_upper_extreme(default_options):
    date = datetime.date(2010, 1, 1)

    config = cli._prepare_config(default_options)

    discount_rate = tasks.DiscountRate(config.snapshot)
    assert discount_rate.get(date) == 0.05


def test_find_exhange_rate_lower_extreme(default_options):
    date = datetime.date(1990, 1, 1)
    currency = "USD"

    config = cli._prepare_config(default_options)

    exchange_rate = tasks.ExchangeRate(config.snapshot)
    assert exchange_rate.get(date, currency) == 1.0


def test_find_exhange_rate_lower_limit(default_options):
    date = datetime.date(1997, 1, 1)
    currency = "USD"

    config = cli._prepare_config(default_options)

    exchange_rate = tasks.ExchangeRate(config.snapshot)
    assert exchange_rate.get(date, currency) == 5.0


def test_find_exhange_rate_base_case(default_options):
    date = datetime.date(1999, 12, 2)
    currency = "USD"

    config = cli._prepare_config(default_options)

    exchange_rate = tasks.ExchangeRate(config.snapshot)
    assert exchange_rate.get(date, currency) == 5.0


def test_find_exhange_rate_upper_limit(default_options):
    date = datetime.date(2002, 2, 1)
    currency = "USD"

    config = cli._prepare_config(default_options)

    exchange_rate = tasks.ExchangeRate(config.snapshot)
    assert exchange_rate.get(date, currency) == 9.0


def test_find_exhange_rate_upper_extreme(default_options):
    date = datetime.date(2010, 1, 1)
    currency = "USD"

    config = cli._prepare_config(default_options)
    exchange_rate = tasks.ExchangeRate(config.snapshot)
    assert exchange_rate.get(date, currency) == 9.0


def test_find_price_lower_extreme(default_options):
    date = datetime.date(1990, 1, 1)
    keyword = "FWPT"

    config = cli._prepare_config(default_options)

    price = tasks.Price(config.snapshot.prices)
    transaction = price.get(date, keyword)
    assert transaction == None


def test_find_price_lower_limit(default_options):
    date = datetime.date(1999, 1, 1)
    keyword = "FWPT"

    config = cli._prepare_config(default_options)

    price = tasks.Price(config.snapshot.prices)
    exchange_rate = tasks.ExchangeRate(config.snapshot)
    transaction = price.get(date, keyword)
    assert transaction.currency == "USD"
    assert transaction._value == -5
    assert transaction.value(exchange_rate) == -25


def test_find_price_base_case(default_options):
    date = datetime.date(1999, 12, 2)
    keyword = "FWPT"

    config = cli._prepare_config(default_options)

    price = tasks.Price(config.snapshot.prices)
    exchange_rate = tasks.ExchangeRate(config.snapshot)
    transaction = price.get(date, keyword)
    assert transaction.currency == "USD"
    assert transaction.value(exchange_rate) == -25


def test_find_price_upper_limit(default_options):
    date = datetime.date(2002, 2, 1)
    keyword = "FWPT"

    config = cli._prepare_config(default_options)

    price = tasks.Price(config.snapshot.prices)
    exchange_rate = tasks.ExchangeRate(config.snapshot)
    transaction = price.get(date, keyword)
    assert transaction.currency == None
    assert transaction._value == -2
    assert transaction.value(exchange_rate) == -2


def test_find_price_upper_extreme(default_options):
    date = datetime.date(2010, 1, 1)
    keyword = "FWPT"

    config = cli._prepare_config(default_options)

    price = tasks.Price(config.snapshot.prices)
    exchange_rate = tasks.ExchangeRate(config.snapshot)
    transaction = price.get(date, keyword)
    assert transaction.currency == None
    assert transaction._value == -2
    assert transaction.value(exchange_rate) == -2


def test_find_price_keyword_not_exists(default_options):
    date = datetime.date(2010, 1, 1)
    keyword = "NOT_A_KEY"

    config = cli._prepare_config(default_options)

    price = tasks.Price(config.snapshot.prices)
    with pytest.raises(AttributeError) as excinfo:
        price.get(date, keyword)

    assert "Price information missing for NOT_A_KEY" in str(excinfo.value)


def test_argparser(parser_mock, copy_npv_testdata_tmpdir):
    output_file = "test"
    input_file = "wells.json"
    start_date = datetime.date(2018, 1, 31)
    end_date = datetime.date(2019, 6, 22)
    ref_date = datetime.date(2018, 4, 5)
    default_discount_rate = 2
    default_exchange_rate = 5.0
    multiplier = 2

    args = [
        "--summary",
        "MOCKED.UNSMRY",
        "--config",
        _CONFIG_FILE,
        "--output",
        output_file,
        "--input",
        input_file,
        "--start-date",
        str(start_date),
        "--end-date",
        str(end_date),
        "--ref-date",
        str(ref_date),
        "--default-discount-rate",
        str(default_discount_rate),
        "--default-exchange-rate",
        str(default_exchange_rate),
        "--multiplier",
        str(multiplier),
    ]
    options = cli.args_parser.parse_args(args)
    config = cli._prepare_config(options)

    assert config.snapshot.files.output_file == output_file
    assert config.snapshot.files.input_file == input_file
    assert config.snapshot.dates.start_date == start_date
    assert config.snapshot.dates.end_date == end_date
    assert config.snapshot.dates.ref_date == ref_date
    assert config.snapshot.default_discount_rate == default_discount_rate
    assert config.snapshot.default_exchange_rate == default_exchange_rate
    assert config.snapshot.multiplier == multiplier
