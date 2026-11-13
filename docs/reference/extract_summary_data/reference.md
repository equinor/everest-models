# Extract Summary Data

There are two ways to use `fm_extract_summary_data`. In the default CLI mode,
the user can request a value at a specific report date using `--output-date` or
`--end-date`. If no selection option is provided, the value at the last available
report date is returned. It is also possible to calculate an aggregate value
using `--aggregation`: `min`, `max`, `mean`, or `median` over a time span. With
no date bounds, the aggregation uses the full time series. If only
`--start-date` is provided, the interval ends at the last report date. If only
`--end-date` is provided, the interval starts at the first report date.
`--diff` calculates the end-date value minus the start-date value and requires
`--start-date`.
`unit-conversion` divides the final value by the selected conversion factor.

Moreover, a YAML configuration allows the user to request several keywords in
one run. `key-section` selects summary keywords, while `fip-section` provides
a user-friendly way to request values for specific FIP regions.

## CLI

```text
fm_extract_summary_data -s SUMMARY -o OUTPUT -k KEY \
		[--start-date START_DATE] [--end-date END_DATE] \
		[--aggregation {max,mean,median,min} | --output-date OUTPUT_DATE | --diff] \
		[--unit-conversion FACTOR] [--lint]
```

`--aggregation` selects a statistic across the full time series or the interval
bounded by `--start-date` and `--end-date`. An omitted bound uses the first or
last report date. `--output-date` selects one exact report date and cannot be
combined with aggregation or interval bounds. `--diff` calculates the end-date
value minus the start-date value and requires `--start-date`. When no selection
option is provided, the last available value is written. `--date` remains an
alias for `--end-date`.

| Selection | Result |
| --- | --- |
| `--output-date DATE` | Value at one exact report date |
| `--aggregation max` | Maximum value over the selected interval or full time series |
| `--aggregation min` | Minimum value over the selected interval or full time series |
| `--aggregation mean` | Arithmetic mean over the selected interval or full time series |
| `--aggregation median` | Median over the selected interval or full time series |
| `--diff` | Value at the end date minus the value at the start date |

The extracted result is written directly to the output file. `--lint` validates
the arguments without writing an output file.
Static target configurations use `--unit-conversion` (or `-u`) when a selected
value needs to be scaled. The factor defaults to `1` and must be non-zero.

## Static Target Configuration

The same command can extract targets described by a YAML configuration. In this
mode, `summary` is the summary file path and output filenames are taken from
the configuration:

```text
fm_extract_summary_data \
		--config CONFIG \
		--summary SUMMARY
```


This mode supports both `fip-section` and `key-section`. Summary keys and
output filenames are supplied by the YAML configuration. Each entry defines
the summary `key` to read and the `output` filename to write. It can also define
`aggregation`, `output-date`, `unit-conversion`, `start-date`, and `end-date`.
When `aggregation` is set, the statistic is calculated over the full time
series, or over the interval bounded by `start-date` and `end-date`. If either
bound is omitted, the first or last report date is used. `output-date` selects
one exact report value and cannot be combined with `aggregation`. If neither is
set, the last available value is selected.

### Configuration schema

The task module also provides typed helpers for extracting multiple scalar
targets from a summary using a YAML configuration. A configuration can contain
`fip-section`, `key-section`, or both.

For `fip-section`, the vector name is constructed as:

$$
			ext{vector} = \text{key} + \text{suffix} + \text{:} + \text{region\_number}
$$

The suffix is the three-character tail of `fip-key` after `FIP`. For
example, `fip-key: FIPNUM`, `key: ROIP`, and `region-number: 2`
selects `ROIPNUM:2`.

```yaml
fip-section:
	- fip-key: FIPNUM
		fip-region:
			- region-number: 1
				output: output/roipnum_1
				aggregation: max
				key: ROIP

key-section:
	- key: FOPT
		output: output/fopt_mean
		aggregation: mean
		unit-conversion: 1000
	- key: FGIT
		output: FGIT-SM3
	- key: FGIT
		output: FGIT-MT
		unit-conversion: 535950843.4
```

`key-section.key` uses the same summary-vector name as the CLI `--key`
option. YAML entries use `aggregation` for `min`, `max`, `mean`, or `median`,
and `output-date` for a specific report date. Date bounds must match summary
report dates. `unit-conversion` is optional and defaults to `1`; the selected
value is divided by it.

## Tasks

::: everest_models.jobs.fm_extract_summary_data.tasks
