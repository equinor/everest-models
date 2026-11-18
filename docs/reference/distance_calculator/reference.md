# Distance Calculator

This EVEREST distance calculator forward model was developed to allow distance calculation between dynamic reservoir properties (such as gas saturation) and objectives, for instance, faults and legacy wells. To allow flexibility, polygonal objectives can be defined using coordinates if they are not defined in ResInsight.

The three calculation types are `fault`, `well`, and `polygon`. Use `name`
for a fault or simulation well and `points` for an open 3D polyline.


The optional `property` mapping selects one dynamic reservoir property, with
one inclusive `threshold` and an optional report `date`. If the date is
omitted, cells that meet the threshold at any report are included. If
`property` is omitted, all active cells are included.

`aggregation` determines how distances from the selected cells to the
objective are summarized: `min`, `max`, `mean`, or `median`. `output`
specifies the file that receives the resulting scalar distance. Distances use
the grid's coordinate units, typically meters. `multiplier` multiplies the
scalar result and map values; `multiplier: 0.001` converts meters to kilometers.
Set `verbose: true` to write a distance map as `<output>_map`. Each calculation
can override the top-level `verbose` setting.


The distance map contains values for all cells in grid 0, not just cells that
passed the optional dynamic-property filter. Load it in ResInsight with
**Add Input Properties**. Non-finite map values are written as zero. For
polygon distances, positive-down depths are adjusted to the grid's Z convention.

## Example

```yaml
{!> reference/distance_calculator/example.yml!}
```

## Configuration schema

This template is generated from the Pydantic config models and can also be
printed with `fm_distance_calculator --schema`.

```yaml
{!> reference/distance_calculator/config.yml!}
```
