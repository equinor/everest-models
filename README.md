# spinningjenny 
[![Spinningjenny](https://github.com/equinor/spinningjenny/workflows/Testing/badge.svg)](https://github.com/equinor/spinningjenny/actions?query=workflow%3A%22Testing%22)

## What is spinningjenny
Forward models and workflows to be used with Ert and Everest

## Download project
The code is hosted on [GitHub](https://github.com/equinor/spinningjenny)

```sh
# Install
pip install git+https://{GH_TOKEN}@github.com/equinor/spinningjenny.git
```

## Run tests
```sh
# Test
pip install --upgrade -r test_requirements.txt
pytest -sv
```

## List of supported workflows:
### drill_planner
```bash
drill_planner -i INPUT -c CONFIG -opt OPTIMIZER [-tl TIME_LIMIT] -o OUTPUT [--ignore-end-date]
```

### npv
```bash
npv -s SUMMARY -c CONFIG [-o OUTPUT] [-i INPUT]
  [-sd START_DATE] [-ed END_DATE] [-rd REF_DATE]
  [-ddr DEFAULT_DISCOUNT_RATE] [-der DEFAULT_EXCHANGE_RATE]
  [--multiplier MULTIPLIER]
```

### rf
```bash
rf -s SUMMARY [-pk PRODUCTION_KEY] [-tvk TOTAL_VOLUME_KEY]
             [-sd START_DATE] [-ed END_DATE] [-o OUTPUT]
```

### schmerge
```bash
fm_schmerge -s SCHEDULE -i INPUT -o OUTPUT
```


### stea
```bash
stea [-c CONFIG]
```


### strip_dates
```bash
strip_dates -s SUMMARY -d [DATES [DATES ...] ] [--allow-missing-dates]
```


### well_constraints
```bash
well_constraints [-h] -i INPUT -c CONFIG [-rc RATE_CONSTRAINTS]
                           [-pc PHASE_CONSTRAINTS] [-dc DURATION_CONSTRAINTS]
                           -o OUTPUT
```


### add_templates
```bash
add_templates -c CONFIG -i INPUT -o OUTPUT
```


### well_filter
```bash
well_filter -i INPUT [-k KEEP] [-r REMOVE] -o OUTPUT
```


### extract_summary_data
```bash
extract_summary_data -s SUMMARY [-sd START_DATE] -ed END_DATE
                               -k KEY [-t {max,diff}] [-m MULTIPLIER] -o
                               OUTPUT
```


### drill_date_planner
```bash
drill_date_planner [-h] -i INPUT -opt OPTIMIZER -b ['UPPER', 'LOWER'] ['UPPER', 'LOWER']
                   -m MAX_DAYS -o OUTPUT
```


### select_wells
```bash
select_wells [-h] -i INPUT [-n WELL_NUMBER | -f WELL_NUMBER_FILE] [-r ['LOWER', 'UPPER']
             ['LOWER', 'UPPER']] [-s ['LOWER', 'UPPER'] ['LOWER', 'UPPER']]
             [-m MAX_DATE] -o OUTPUT
```
