# 0.2.0
 * | The command line argument for fm_schmerge has changed.
   | This is more in line with how the other jobs behave

    * -i, --input renamed to -s, --schedule
    * -c, --config renamed to -i, --input
 * Added the extract_summary_data job

# 0.1.6
 * Make drill planner interval bounds exclusive. Previous implementation
   would permit overlapping intervals.
 * Some minor clean-up, removing dead code.
 * Add NPV calculation for completion dates. In the case where a lower
   priority well can be drilled before a higher priority well, the end date
   is shifted. The NPV calculation now reflects this, but using the date
   that the well is drilled instead of when it is opened.
 * Reverted the extract_summary_data job for now, this functionality will be
   further discussed before it is released.

# 0.1.5
 * Improve or-tool drillplanner implementation
 * Add missing config key handling to schmerge job
 * Ignore well costs in the NPV job if file with well dates is not
   supplied
 * Outputfile no longer required for recovery factor job (outputs
   to standard out if not supplied)
 * Add templates job will now stop and return an error for mismatched
   templates (used to only submit a warning)
 * Add extract summary data job

# 0.1.4
 * Improved argument validation for the RF job (checks if files are
   writable)
 * RF result is also included in the log (stdout)
 * Changed date format for RF to be consistent with ISO8601 (was
   DD.MM.YYYY, is now YYYY-MM-DD)
 * NPV no longer has a default input file (was wells.json). Instead it
   is required
 * Improved schmerge DATES recognition (now handles multiple whitespace,
   allows JLY (for JUL), and hour:minute:second formatting)
 * Minor bug fixes

# 0.1.3
 * Add drill delay to greedy drill planner
 * Handle single digit input format in schmerge job
 * Allow uncompleted tasks in greedy drill_planner
 * Expose list of jobs (for external libraries)
 * Add additional tests for entire workflow
 * Handle no dates in user input for schmerge job
 * Add well_filter and well_drill executables

# 0.1.2
 * Refactor the two drill_planner implementations for syngergies
 * Include well prioritization validation for drill_planner schema
 * Handle python2.7 issue with date (must be fixed to 1900)
 * Make overlap boundaries not inclusive for drill_planner
 * Improve test cases
 * Add specific debug messages to drill_planner
 * Add well filter job

# 0.1.1
 * Fix package discovery

# 0.1.0
The first release contains a handful of forward model jobs that can be
combined in order to process control values from everest and together
with user configurations, provide sensible input files for reservoir
simulators. Each forward model contains their own description.
