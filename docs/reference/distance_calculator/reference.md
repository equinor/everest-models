# Distance Calculator

This EVEREST distance calculator forward model was developed to allow distance calculation between dynamic reservoir properties (such as gas saturation) and objectives, for instance, faults and legacy wells. To allow flexibility, polygonal objectives can be defined using coordinates if they are not defined in ResInsight.

The three distance calculation types are `fault-distance`, `well-distance`, and `polygon-distance`.


Use `property` to select a dynamic reservoir property, such as gas saturation.
`property-threshold` sets the minimum value a cell must reach to be included
in the distance calculation. `output-date` selects the report date used for
this filter. If no date is specified, cells that meet the threshold at any
available timestep are included.

`aggregation` determines how distances from the selected cells to the
objective are summarized: `min`, `max`, `mean`, or `median`. `output-name`
specifies the file that receives the resulting scalar distance. Distances use
the grid's coordinate units, typically meters. `unit-conversion` divides the
scalar result and map values by the supplied factor, following the same
convention as Extract Summary Data. For example, with meter-based grid
coordinates, `unit-conversion: 1000` writes distances in kilometers. Set
`printing-distance-map` to `true` to also write each cell's distance to the
objective; this map can be loaded into ResInsight using **Add Input Properties**.


## Configuration Keywords

| Keyword | Description |
| --- | --- |
| `distance-calculations` | Required non-empty list. Each item defines one distance calculation. |
| `type` | Required target kind: `fault-distance`, `well-distance`, or `polygon-distance`. |
| `fault-name` | Required for `fault-distance`. Name of the fault in the loaded ResInsight case. |
| `well-name` | Required for `well-distance`. Name of a simulation well; distance is measured to its connected cells across the simulation timesteps. |
| `polygon-input` | Required for `polygon-distance`. At least two points, each given as `easting, northing, depth` in grid coordinate units. Consecutive points form an open 3D polyline; the distance is to its nearest segment. |
| `property` | Optional dynamic grid property used to select active cells. A scalar, comma-separated string, or list is accepted. If omitted, all active cells are selected and `output-date` is ignored. |
| `property-threshold` | Optional inclusive lower bound for `property` (`value >= threshold`); defaults to `0.0`. A scalar applies to all properties; a list pairs thresholds with properties, reusing its last value if needed. |
| `output-date` | Optional report date for the dynamic property filter. If omitted, cells meeting the threshold at any available timestep are included. A scalar applies to all properties; a list pairs dates with properties, reusing its last value if needed. Dates must match report dates. |
| `aggregation` | Optional statistic over finite, positive distances for selected cells: `min`, `max`, `mean`, or `median`. Defaults to `min`. |
| `unit-conversion` | Optional non-zero numeric factor by which the scalar distance and any distance-map values are divided. Defaults to `1`; the alias `u` is also accepted. |
| `output-name` | Required output filename for the scalar result. The file contains one numeric value. |
| `printing-distance-map` | Optional boolean controlling the per-cell distance map. Defaults to `false`; when `true`, writes an Eclipse-style property file named `<output-name>_map`. |

The distance map contains values for all cells in grid 0, not just cells that
passed the optional dynamic-property filter. Non-finite map values are written
as zero. For polygon distances, positive-down input depths are adjusted to the
loaded grid's Z convention.

`printing-distance-map` may also be set at the top level to provide the default
for calculations that do not specify it individually; the top-level default is
also `false`.
