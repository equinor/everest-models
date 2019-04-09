#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import datetime
import logging
import math
import os.path
import re
import sys
from itertools import compress

from ecl.summary import EclSum

import yaml
from spinningjenny import customized_logger

logger = customized_logger.get_logger(__name__)


class CalculateNPV:
    """
    Module to calculate the NPV based on an eclipse simulation. Main purpose
    of this class is to gather the different artifacts from configfile,
    run the npv calculation and then write the result to file.

    """

    def __init__(self, input_data):
        self.ecl_sum = EclSum(input_data.get('files').get('summary_file'))
        self.output_file = input_data.get('files').get('output_file')
        self.multiplier = input_data.get('multiplier')
        self._npv = 0.0
        self.exchange_rate = ExchangeRate(input_data)
        self.discount_rate = DiscountRate(input_data)
        self.price = Price(input_data)
        self.date_handler = DateHandler(input_data, self.ecl_sum)
        self.cost = Cost(input_data)
        self.keywords = Keywords(input_data, self.ecl_sum).get()

    def run(self):
        time_range = self.date_handler.time_range
        ref_date = self.date_handler.ref_date
        logger.info("running npv calculation with time_range {} - {} and ref_date {}".format(
            self.date_handler.start_date, self.date_handler.end_date, ref_date))
        blocked_production = self._extract_blocked_production(time_range)
        self._extract_prices(blocked_production, time_range, ref_date)
        self._extract_costs(ref_date)
        logger.info(
            "done calculating, writing result {} to output".format(self.npv))

    @property
    def npv(self):
        return round(self.multiplier * self._npv, 2)

    def _extract_costs(self, ref_date):
        for cost in self.cost.get():
            cost_exhanged = cost.value(self.exchange_rate)
            self._npv -= self._npv_calc(cost_exhanged, cost.date, ref_date)

    def _extract_prices(self, blocked_production, time_range, ref_date):
        for idx, date in enumerate(time_range[1:]):
            current_date = date.datetime()

            total_npv = 0
            for keyword in self.keywords:
                transaction = self.price.get(current_date, keyword)
                price_exchanged = transaction.value(self.exchange_rate)
                total_npv += blocked_production[keyword][idx] * price_exchanged
            self._npv += self._npv_calc(total_npv, current_date, ref_date)

    def _extract_blocked_production(self, time_range):
        blocked_production = {}
        for keyword in self.keywords:
            blocked_production[keyword] = self.ecl_sum.blocked_production(
                keyword, time_range)
        return blocked_production

    def _npv_calc(self, value, date, ref_date):
        discount_rate = self.discount_rate.get(date)
        return value / (1.0 + discount_rate) ** ((date - ref_date).days / 365.25)

    def write(self):
        with open(self.output_file, 'w') as f:
            f.write('{0:.2f}'.format(self.npv))


class Transaction:
    """
    Class handling prices and costs in a unified way regards to date, value and currency

    """

    def __init__(self, date, value, currency):
        self.date = date
        self._value = value
        self.currency = currency

    @classmethod
    def using_cost(cls, cost_entry):
        date = _str2date(cost_entry['date'])
        value = cost_entry['value']
        currency = cost_entry.get('currency', None)
        return cls(date, value, currency)

    @classmethod
    def using_well_cost(cls, well_cost_entry, t2s_entries, well_name):
        date = _str2date(t2s_entries[well_name])
        value = well_cost_entry['value']
        currency = well_cost_entry.get('currency', None)
        return cls(date, value, currency)

    @classmethod
    def using_price(cls, price_entry, date):
        value = price_entry['value']
        currency = price_entry.get('currency', None)
        return cls(date, value, currency)

    @classmethod
    def empty(cls):
        return cls(None, 0, None)

    def value(self, exchange_rate):
        return exchange_rate.get(self.date, self.currency) * self._value


class Keywords:
    """
    Class handling keywords
    If any keys specified in config file - extract and validate.
    If key specified is not present in simulation summary data - raise Exception.

    """

    def __init__(self, input_data, ecl_sum):
        summary_keys = input_data.get('summary_keys', None)

        if summary_keys:
            keys_exists = [not ecl_sum.has_key(key) for key in summary_keys]
            if all(keys_exists):
                missing_keys = list(compress(summary_keys, keys_exists))
                raise AttributeError(
                    'Missing required data ({}) in summary file.'.format(missing_keys))
            self._keywords = summary_keys
            logger.info(
                "using keywords from 'summary_keys' {}".format(self._keywords))
        else:
            self._keywords = list(input_data['prices'].keys())
            logger.info("'summary_keys' not found, defaulting to keys from prices {}".format(
                self._keywords))

    def get(self):
        return self._keywords


class ExchangeRate:
    """
    Class handling exchange rates. If no exchange rate specified for currency
    we defaults to 1

    """

    def __init__(self, input_data):
        self._exchange_rates = input_data.get('exchange_rates', [])
        self.default_exchange_rate = input_data.get('default_exchange_rate')

    def get(self, date, currency):
        if currency and currency in self._exchange_rates:
            ordered_data = sorted(self._exchange_rates[currency], key=lambda entry: _str2date(
                entry['date']), reverse=True)
            for entry in ordered_data:
                if _str2date(entry['date']) <= date:
                    return entry['value']
        logger.warn("entry for exchange_rate {} {} does not exist, using default {}".format(
            date, currency, self.default_exchange_rate))
        return self.default_exchange_rate


class DiscountRate:
    """
    Class handling discount rates. If no discount rates are provided, we use a default

    """

    def __init__(self, input_data):
        self._discount_rates = input_data.get('discount_rates', [])
        self.default_discount_rate = input_data.get('default_discount_rate')

    def get(self, date):
        ordered_data = sorted(self._discount_rates, key=lambda entry: _str2date(
            entry['date']), reverse=True)
        for entry in ordered_data:
            if _str2date(entry['date']) <= date:
                return entry['value']
        logger.warn("entry for discount rate {} does not exist, using default {}".format(
            date, self.default_discount_rate))
        return self.default_discount_rate


class Price:
    """
    Class handling prices for different keywords and wraps all these inn a common
    "transaction" format to be handled equally later on.

    If key provided in config not having a price attached to it - we are throwing
    exception.

    """

    def __init__(self, input_data):
        self._prices = []
        if 'prices' not in input_data:
            raise AttributeError(
                'Price information is required to do an NPV calculation\n')
        self._prices = input_data['prices']

    def get(self, date, keyword):
        if keyword not in self._prices:
            raise AttributeError(
                'Price information missing for %s\n' % (keyword))

        ordered_data = sorted(self._prices[keyword], key=lambda entry: _str2date(
            entry['date']), reverse=True)

        for entry in ordered_data:
            if _str2date(entry['date']) <= date:
                return Transaction.using_price(entry, date)

        logger.warn('Price information missing at %s for %s. Using value 0.' % (
            date.strftime('%d.%m.%Y'), keyword))
        return Transaction.empty()


class Cost:
    """
    Class handling both cost and well-cost and wraps all these inn a common
    "transaction" format to be handled equally later on.

    Well-costs are only taken into account if the well is specified in the
    corresponding t2s_npv_info file generated by the t2s script

    """

    def __init__(self, input_data):
        t2s_file_path = input_data['files']['t2s_file']

        self._costs = []
        if 'costs' in input_data:
            for cost_entry in input_data['costs']:
                self._costs.append(Transaction.using_cost(cost_entry))

        if 'well_costs' in input_data:
            _t2s = {}
            logger.debug("open t2s-file from {}".format(t2s_file_path))
            with open(t2s_file_path, 'r') as t2s_file:
                for line in t2s_file:
                    date, well = str.strip(line).split(" ")
                    _t2s[well] = date

            for well_cost_entry in input_data['well_costs']:
                well_name = well_cost_entry['well']
                if well_name in _t2s:
                    self._costs.append(Transaction.using_well_cost(
                        well_cost_entry, _t2s, well_name))
                else:
                    logger.warn(
                        'Well cost for well {} skipped due to lacking reference in t2s'.format(well_name))

    def get(self):
        return self._costs


class DateHandler:
    """
    Class handling dates.
    Basically - if provided in config file - use those - otherwise use
    simulation start or / and end dates.

    Dates are also validated against rules fetched from old npv-script

    """

    def __init__(self, input_data, ecl_summary):
        self._ecl_summary = ecl_summary
        self.start_date = ecl_summary.start_time
        self.end_date = ecl_summary.end_time
        self.ref_date = self.start_date

        if 'dates' in input_data:
            dates = input_data.get('dates')
            if 'start_date' in dates:
                configured_start = dates.get('start_date')
                self.start_date = _str2date(configured_start)
                logger.info(
                    "simulation start_date set {}".format(configured_start))
            else:
                logger.info("Simulation start date defaults to summary start date: {}".format(
                    self.start_date))

            if 'end_date' in dates:
                configured_end = dates.get('end_date')
                self.end_date = _str2date(configured_end)
                logger.info(
                    "simulation end_date set {}".format(configured_end))
            else:
                logger.info(
                    "Simulation end date defaults to summary end date: {}".format(self.end_date))

            if 'ref_date' in dates:
                configured_ref = dates.get('ref_date')
                self.ref_date = _str2date(configured_ref)
                logger.info(
                    "simulation ref_date set {}".format(configured_ref))
            else:
                logger.info(
                    "Simulation ref date defaults to summary start date: {}".format(self.ref_date))
        else:
            logger.info(
                "no dates provided, defaulting to simulation start and end dates {} - {}. ref date is {}".format(self.start_date, self.end_date, self.ref_date))

        self.time_range = self._ecl_summary.timeRange(
            start=self.start_date, end=self.end_date, interval='1d')

        if (self._ecl_summary.start_time > self.start_date) \
                or (self._ecl_summary.end_time < self.end_date):
            logger.warn("""The date range ({} - {}) is not during the simulation time ({} - {}).\n
                            Effective date range defaults to simulation start and end dates {} - {}""".format(
                        self.start_date.strftime('%d.%m.%Y'),
                        self.end_date.strftime('%d.%m.%Y'),
                        self._ecl_summary.start_time.strftime('%d.%m.%Y'),
                        self._ecl_summary.end_time.strftime('%d.%m.%Y'),
                        self._ecl_summary.start_time.strftime('%d.%m.%Y'),
                        self._ecl_summary.end_time.strftime('%d.%m.%Y')))


def _str2date(datestr):
    return datetime.datetime.strptime(datestr, '%d.%m.%Y')
