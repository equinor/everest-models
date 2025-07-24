


import datetime
import itertools
import logging
from abc import ABC, abstractmethod
from functools import partial
from typing import Any, Callable, Dict, Iterable, Optional, Protocol, Tuple, Union

from resdata.summary import Summary
from resdata.util.util import TimeVector

from .economic_indicator_config_model import EconomicIndicatorConfig
from everest_models.jobs.fm_compute_economics.parser import build_argument_parser

logger = logging.getLogger(__name__)

__all__ = ["EconomicIndicatorCalculatorABC"]


CONVERTION_CUBIC_METERS_TO_BBL = 6.289814



class Rate(Protocol):
    date: datetime.date
    value: float
    currency: str


class Production(Protocol):
    def blocked_production(self, totalKey, timeRange): ...


def _rate_sort_reverse_dates(rates: Iterable[Rate]) -> Iterable[Rate]:
    return sorted(rates, key=lambda rate: rate.date, reverse=True)


def _get_rate(rates: Iterable[Rate], date: datetime.date, default: float) -> float:
    for rate in _rate_sort_reverse_dates(rates):
        if rate.date <= date:
            return rate.value
    return default


def _get_ref_date(summary_start_date: datetime.date, start_date: datetime.date):
    return (
        summary_start_date
        if not start_date or summary_start_date > start_date
        else start_date
    )


def _get_blocked_production(
    ctx: Production, keys: Iterable[str], time_range: TimeVector
) -> Dict[str, Any]:
    partial(ctx.blocked_production, timeRange=time_range)
    try:
        return {keyword: ctx.blocked_production(keyword, time_range) for keyword in keys}
    except Exception as e:
        logger.error(f"Error in _get_blocked_production: {e}")
        print(f"Error in _get_blocked_production: {e}")  # Debug info
        raise e


class EclipseSummary:
    
    def __init__(self, config) -> None:
       
        logger.debug("Initializing EclipseSummary...")
        args_parser = build_argument_parser()
        options = args_parser.parse_args(args=None)
        if options.lint:
            args_parser.exit()

        parsed_arguments = vars(options)
        print("parsed_arguments",parsed_arguments)
        case_name_self = parsed_arguments.get('case_name') 
        if ".UNSMRY" not in case_name_self:
            case_name_self += ".UNSMRY"
        self.main = self.get_summary(case_name_self)
        logger.debug(f"Main UNSMRY 1: {case_name_self}")
        logger.debug(f"Main UNSMRY 2: {self.main}")

        case_name_reference = parsed_arguments.get('summary_reference') 
        if ".UNSMRY" not in case_name_reference:
            case_name_reference += ".UNSMRY"
        self.reference = self.get_summary(case_name_reference)
        logger.debug(f"Reference UNSMRY 1: {case_name_reference}")
        logger.debug(f"Reference UNSMRY 2: {self.reference}")
  
        print("Config.summary.keys", config.summary.keys)
        self.keys = self.get_keys(config.summary.keys)
        

    

    @property
    def dates(self) -> Tuple[Any, Any, Any]:
        if self.main is None:
            return (None, None, None)
        return (self.main.start_date, self.main.end_date, self.main.time_range)

    @staticmethod
    def _get_keywords(
        summary_keys: Iterable[str], func: Callable[[str], bool]
    ) -> Tuple[str, ...]:
        try:
            # Debugging prints
            print(f"summary_keys type: {type(summary_keys)}, value: {summary_keys}")
            print(f"func type: {type(func)}, value: {func}")

            # Ensure `summary_keys` is actually iterable
            if not isinstance(summary_keys, (list, tuple, set)):
                raise TypeError(f"Expected an iterable for summary_keys, but got {type(summary_keys)}")

            # Ensure `func` is callable
            if not callable(func):
                raise TypeError(f"Expected a callable function for func, but got {type(func)}")

            # Process normally
            if all(missing_keys := [func(key) for key in summary_keys]):
                raise AttributeError(
                    f"Missing required data ({list(itertools.compress(summary_keys, missing_keys))}) in summary file."
                )
            
            return tuple(summary_keys)

        except Exception as e:
            logger.error(f"Error in _get_keywords: {e}")
            print(f"Error in _get_keywords: {e}")  # Debug info
            raise e


    def get_summary(self, filepath: Union[str, None]) -> Union[Summary, None]:
        try:
            return Summary(str(filepath)) if filepath else None
        except Exception as e:
            logger.error(f"Error in get_summary for filepath {filepath}: {e}")
            print(f"Error in get_summary for filepath {filepath}: {e}")  # Debug info
            raise e

    def get_keys(self, config_keys: Tuple[str, ...]) -> Tuple[str, ...]:
        try:
            main_keywords = self._get_keywords(
                config_keys, lambda key: not self.main.has_key(key)
            )
            reference_keywords = (
                main_keywords
                if self.reference is None
                else self._get_keywords(
                    config_keys, lambda key: not self.reference.has_key(key)
                )
            )

            if set(main_keywords) != set(reference_keywords):
                raise AttributeError("unconsistent keys between main and reference summary")

            return main_keywords
        except Exception as e:
            logger.error(f"Error in get_keys: {e}")
            print(f"Error in get_keys: {e}")  # Debug info
            raise e


    def get_delta_blocked_productions(self, time_range: TimeVector):
        try:
            try:
                blocked_productions = _get_blocked_production(self.main, self.keys, time_range)
                #print(f"Blocked Productions (Initial): {blocked_productions}")

            except Exception as e:
                print("ERROR: Exception while calling _get_blocked_production for main")
                raise e

            if isinstance(self.reference, Summary):
                try:
                    ref_blocked_productions = _get_blocked_production(self.reference, self.keys, time_range)

                    # Print volumes before subtraction
                    for key in self.keys:
                        main_vals = blocked_productions.get(key)
                        ref_vals = ref_blocked_productions.get(key)

                        if main_vals is not None and ref_vals is not None:
                            main_sum = sum(main_vals)
                            ref_sum = sum(ref_vals)
                           
                            print(f"[{key}] Main total volume: {main_sum:,.0f}, Reference total volume: {ref_sum:,.0f}, Difference: {(main_sum - ref_sum):,.0f}")
                           

                        else:
                            print(f"[{key}] Missing data in either main or reference summary.")

                    # Subtract after logging
                    blocked_productions = {
                        key: blocked_productions[key] - ref_blocked_productions[key]
                        for key in self.keys
                    }

                except RuntimeError as re:
                    logger.error(f"RuntimeError in get_delta_blocked_productions: {re}")
                    print(f"RuntimeError in get_delta_blocked_productions: {re}")
                    print("summary and reference summary files are not consistent")

            return blocked_productions

        except Exception as e:
            logger.error(f"Error in get_delta_blocked_productions: {e}")
            print(f"Error in get_delta_blocked_productions: {e}")  # Debug info
            #traceback.print_exc()  # Print full error stack
            raise e
            

class EconomicIndicatorCalculatorABC(ABC):
    def __init__(self, config: EconomicIndicatorConfig) -> None:
        try:
            self.config = config
            self.summary = EclipseSummary(config)
        except Exception as e:
            logger.error(f"Error initializing EconomicIndicatorCalculatorABC: {e}")
            print(f"Error initializing EconomicIndicatorCalculatorABC: {e}")  # Debug info
            raise e

    def _get_output_exchange_rate(self, date: datetime.date) -> float:
        try:
            if self.config.output.currency_rate is None:
                return self.config.default_exchange_rate
            return _get_rate(
                itertools.chain(self.config.output.currency_rate),
                date,
                self.config.default_exchange_rate,
            )
        except Exception as e:
            logger.error(f"Error in _get_output_exchange_rate: {e}")
            print(f"Error in _get_output_exchange_rate: {e}")  # Debug info
            raise e

    def _get_exchange_rate(
        self, date: datetime.date, currency: Optional[str] = None
    ) -> float:
        try:
            to_output = self._get_output_exchange_rate(date)
            if currency is None:
                return self.config.default_exchange_rate * to_output
            return (
                _get_rate(
                    itertools.chain(self.config.exchange_rates.get(currency, [])),
                    date,
                    self.config.default_exchange_rate,
                )
                * to_output
            )
        except Exception as e:
            logger.error(f"Error in _get_exchange_rate: {e}")
            print(f"Error in _get_exchange_rate: {e}")  # Debug info
            raise e

    def _discount(self, economic_indicator: float, date: datetime.date) -> float:
        try:
            discount_rate = _get_rate(
                self.config.discount_rates, date, self.config.default_discount_rate
            )
            return economic_indicator / (1 + discount_rate) ** (
                (date - self.ref_date).days / 365.25
            )
        except Exception as e:
            logger.error(f"Error in _discount: {e}")
            print(f"Error in _discount: {e}")  # Debug info
            raise e

    def _get_dates(self) -> Tuple[datetime.date, datetime.date, datetime.date]:
        try:
            start, end, _ = self.summary.dates
            return (
                (start, end, start)
                if not self.config.dates
                else (
                    self.config.dates.start_date or start,
                    self.config.dates.end_date or end,
                    self.config.dates.ref_date
                    or _get_ref_date(start, self.config.dates.start_date),
                )
            )
        except Exception as e:
            logger.error(f"Error in _get_dates: {e}")
            print(f"Error in _get_dates: {e}")  # Debug info
            raise e

    def _extract_discounted_costs(self, well_dates: Dict[str, datetime.date]) -> float:
        try:
            def get_costs():
                return itertools.chain(
                    (
                        (
                            self._get_exchange_rate(cost.date, cost.currency) * cost.value,
                            cost.date,
                        )
                        for cost in self.config.costs
                    ),
                    (
                        (
                            self._get_exchange_rate(well_dates[entry.well], entry.currency)
                            * entry.value,
                            well_dates[entry.well],
                        )
                        for entry in self.config.well_costs
                        if entry.well in well_dates
                    )
                    if self.config.well_costs and well_dates
                    else [],
                )

            return sum(self._discount(*cost) for cost in get_costs())
        except Exception as e:
            logger.error(f"Error in _extract_discounted_costs: {e}")
            print(f"Error in _extract_discounted_costs: {e}")  # Debug info
            raise e

    @abstractmethod
    def _compute(
        self,
        well_dates: Dict[str, datetime.date],
        start: datetime.date,
        end: datetime.date,
    ) -> float:
        raise NotImplementedError

    def compute(self, well_dates: Dict[str, datetime.date]) -> float:
        try:
            start, end, self.ref_date = self._get_dates()
            return round(self._compute(well_dates, start, end) * self.config.multiplier, 2)
        except Exception as e:
            logger.error(f"Error in compute method: {e}")
            logger.error(f"Reference and Self case might be identical. Or Remap might not specified")
            print(f"Error in compute method: {e}")  # Debug info
            print(f"Reference and self case might be identical")  # Debug info
            raise e


class NPVCalculator(EconomicIndicatorCalculatorABC):
    def _get_price(self, date: datetime.date, keyword: str) -> Optional[float]:
        try:
            if keyword not in self.config.prices:
                raise AttributeError(f"Price information missing for {keyword}")

            for tariff in _rate_sort_reverse_dates(
                itertools.chain(self.config.prices[keyword]),
            ):
                if tariff.date <= date:
                    return self._get_exchange_rate(date, tariff.currency) * tariff.value

            logger.warning(f"Price information missing at {date} for {keyword}.")
        except Exception as e:
            logger.error(f"Error in _get_price for {keyword} at {date}: {e}")
            print(f"Error in _get_price for {keyword} at {date}: {e}")  # Debug info
            raise e

    def _extract_discounted_prices(self, time_range: TimeVector) -> float:
        try:
            blocked_productions = self.summary.get_delta_blocked_productions(time_range)
            return sum(
                self._discount(
                    sum(
                        blocked_productions[keyword][index] * transaction
                        for keyword in self.summary.keys
                        if (transaction := self._get_price(date.date(), keyword))
                        is not None
                    ),
                    date.date(),
                )
                for index, date in enumerate(time_range[1:])
            )
        except Exception as e:
            logger.error(f"Error in _extract_discounted_prices: {e}")
            print(f"Error in _extract_discounted_prices: {e}")  # Debug info
            raise e

    def _compute(
            self,
            well_dates: Dict[str, datetime.date],
            start: datetime.date,
            end: datetime.date,
        ) -> float:
            try:
                time_range = self.summary.main.time_range(start, end, interval="1d")

                gross_npv = self._extract_discounted_prices(time_range)
                costs = self._extract_discounted_costs(well_dates)
                net_npv = gross_npv - costs

                print()
                print("Gross NPV: {:,.0f}".format(gross_npv))
                print("Costs: {:,.0f}".format(costs))
                print("Net NPV: {:,.0f}".format(net_npv))
              
                

                return net_npv

            except Exception as e:
                logger.error(f"Error in _compute (NPVCalculator): {e}")
                print(f"Error in _compute (NPVCalculator): {e}")  # Debug info
                raise e

      

class BEPCalculator(EconomicIndicatorCalculatorABC):
    def __init__(self, config: EconomicIndicatorConfig) -> None:
        try:
            super().__init__(config)
        except Exception as e:
            logger.error(f"Error initializing BEPCalculator: {e}")
            print(f"Error initializing BEPCalculator: {e}")  # Debug info
            raise e


    def _get_price(self, date: datetime.date, keyword: str) -> Optional[float]:
        try:
            if keyword not in self.config.prices:
                raise AttributeError(f"Price information missing for {keyword}")

            for tariff in _rate_sort_reverse_dates(
                itertools.chain(self.config.prices[keyword]),
            ):
                if tariff.date <= date:
                    return self._get_exchange_rate(date, tariff.currency) * tariff.value

            logger.warning(f"Price information missing at {date} for {keyword}.")
        except Exception as e:
            logger.error(f"Error in _get_price for {keyword} at {date}: {e}")
            print(f"Error in _get_price for {keyword} at {date}: {e}")  # Debug info
            raise e

    def _get_oil_equivalent(self, blocked_productions):
        try:
            oil_equivalent = {}
            total_equivalent = 0  # Initialize sum for total oil equivalent

            total_oil_production_difference = 0
            total_gas_production_difference = 0
            total_water_production_difference = 0

            total_oil_production_difference += sum(blocked_productions.get('FOPT', 0))
            total_gas_production_difference += sum(blocked_productions.get('FGPT', 0))
            total_water_production_difference += sum(blocked_productions.get('FWPT', 0))

            print("Total oil production difference:", total_oil_production_difference)
            print("Total gas production difference:", total_gas_production_difference)
            print("Total water production difference:", total_water_production_difference)
        

            for input_phase, output_phases in self.config.oil_equivalent.remap.items():
                print(f"\nProcessing input_phase: {input_phase}")
                print("Corresponding output phases:", output_phases)
                

                blocked_production = blocked_productions.get(input_phase, 0)
                #print(f"  - blocked_production ({input_phase}) = {blocked_production}")

                for output_phase, equivalent in output_phases.items():
                    oil_conversion_factor = self.config.oil_equivalent.oil.get(output_phase, 1)
                    conversion_factor = CONVERTION_CUBIC_METERS_TO_BBL

                    oil_equivalent[output_phase] = (
                        blocked_production * equivalent * oil_conversion_factor * conversion_factor
                    )

                    # Convert DoubleVector to a single total sum
                    total_phase_equivalent = sum(oil_equivalent[output_phase])  

                    # Accumulate total oil equivalent
                    total_equivalent += total_phase_equivalent

                    # Print only the total for this phase
                    print(f"Total oil equivalent for {output_phase}: {total_phase_equivalent:,.0f}")
                

            print("\nTotal oil equivalent =", total_equivalent)
            return oil_equivalent

        except Exception as e:
            logger.error(f"Error in _get_oil_equivalent: {e}")
            print(f"ERROR in _get_oil_equivalent: {e}")  # Debug info
            raise e

  

    def _extract_discounted_opex(self, time_range: TimeVector) -> float:
        keywords = ['FWPT', 'FWIT', 'FGIT']
        blocked_productions = self.summary.get_delta_blocked_productions(time_range)
        total_discounted_cost = 0.0
        last_unit_prices = {}
        last_printed_unit_prices = {}  # Track what was printed
        costs_per_keyword = {}  # New: track final cost per keyword

        print("\nCalculating costs associated to ['FWPT', 'FWIT', 'FGIT']: ")

        for keyword in keywords:
            if keyword not in blocked_productions:
                print(f"Skipping keyword '{keyword}': not in blocked productions.")
                continue

            values = blocked_productions[keyword]

            for index, date in enumerate(time_range[1:]):
                try:
                    if index >= len(values):
                        if keyword not in last_unit_prices:
                            print(f"Skipping keyword '{keyword}': no value at index {index}.")
                        continue

                    date_obj = date.date()
                    volume = values[index]
                    unit_price = self._get_price(date_obj, keyword) or 0.0
                    last_unit_prices[keyword] = unit_price

                    # Only print if the unit price changed or if it's the first print for this keyword
                    if (keyword not in last_printed_unit_prices or
                            last_printed_unit_prices[keyword] != unit_price):
                        print(f"[{date_obj}] {keyword}: unit_price={unit_price}")
                        last_printed_unit_prices[keyword] = unit_price

                    discounted_value = self._discount(volume * unit_price, date_obj)
                    total_discounted_cost += discounted_value
                    costs_per_keyword[keyword] = costs_per_keyword.get(keyword, 0.0) + discounted_value

                except Exception as e:
                    print(f"Error for keyword '{keyword}' at index {index}, date {date}: {e}")

        # Print final cost per keyword
        for keyword in keywords:
            if keyword in costs_per_keyword:
                
                print(f"[FINAL] Total discounted cost for '{keyword}': {costs_per_keyword[keyword]:,.0f}")
                
                            
        print(f"[TOTAL] Discounted cost for all keywords: {total_discounted_cost:.0f}\n")
        return total_discounted_cost


  
    
    def _extract_discounted_production(self, time_range: TimeVector) -> float:

        try:
            blocked_productions = self.summary.get_delta_blocked_productions(time_range)

            oil_equivalent = self._get_oil_equivalent(blocked_productions)
            total_discounted_production = 0  # Track running total

            for index, date in enumerate(time_range[1:]):
                try:
                    production_sum = sum(
                        oil_equivalent[keyword][index]
                        for keyword in self.config.oil_equivalent.oil
                    )
                    discounted_value = self._discount(production_sum, date.date())

   
                    total_discounted_production += discounted_value

                except Exception as e:
                    print(f"Error at index {index}, date {date}: {e}")

            print(f"Total Discounted Production: {total_discounted_production}")
            return total_discounted_production

        except Exception as e:
            logger.error(f"Error in _extract_discounted_production: {e}")
            print(f"Error in _extract_discounted_production: {e}")  # Debug info
            raise e

       

    def _compute(
            self,
            well_dates: Dict[str, datetime.date],
            start: datetime.date,
            end: datetime.date,
        ) -> float:
            args_parser = build_argument_parser()
            options = args_parser.parse_args(args=None)

            print("bep_consider_opex =", options.config.bep_consider_opex)

            try:
                time_range = self.summary.main.time_range(start, end, interval="1d")
                costs = self._extract_discounted_costs(well_dates)
                production = self._extract_discounted_production(time_range)
                opex = self._extract_discounted_opex(time_range)

                if options.config.bep_consider_opex is True:
                    # BEP includes OPEX
                    bep_value = (costs - opex) / production
                    print("[USED] BEP with OPEX:", bep_value, "Capex costs:", costs, "Opex costs:", opex )


                    # Debug: show what it would be without OPEX
                    bep_wo_opex = costs / production
                    print("[NOT USED] BEP without OPEX:", bep_wo_opex, "Capex costs:", costs, "Opex costs:" ,opex )

                else:
                    # BEP without OPEX
                    bep_value = costs / production
                    print("[USED] BEP without OPEX:", bep_value, "Capex costs:", costs, "Opex costs:", opex )

                    # Debug: show what it would be with OPEX
                    bep_with_opex = (costs - opex) / production
                    print("[NOT USED] BEP with OPEX:", bep_with_opex,"Capex costs:", costs, "Opex costs:", opex )

                # Clamp to 99 if result is negative
                return max(bep_value, 99) if bep_value < 0 else bep_value

            except Exception as e:
                logger.error(f"Error in _compute (BEPCalculator): {e}")
                print(f"Error in _compute (BEPCalculator): {e}")  # Debug info
                raise e  # Ensure this is correctly aligned



# The keys of the INDICATORS dictionary should be consistent with the choices given to argparse in parser.py
INDICATORS = {"npv": NPVCalculator, "bep": BEPCalculator}


def create_indicator(
    calculation: str, config: EconomicIndicatorConfig
) -> Union[NPVCalculator, BEPCalculator]:
    try:
        if calculation not in INDICATORS:
            raise ValueError(
                f"Invalid indicator: {calculation} ---  Select from {INDICATORS.keys()} "
            )

        return INDICATORS[calculation](config)
    except Exception as e:
        logger.error(f"Error in create_indicator: {e}")
        print(f"Error in create_indicator: {e}")  # Debug info
        raise e