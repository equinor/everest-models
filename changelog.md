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
