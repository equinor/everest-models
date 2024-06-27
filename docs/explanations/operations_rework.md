# Operations Rework

## Issue

There are some forward models that were hacked by modifying the input file JSON key `ops` (operations).
The `ops` key holds a list of dictionary objects, each `op` object can hold an arbritary key value pair.
This flexibility allowed users to use the forward model outside of its intended purpose and/or scope.
The introduction of parsing, linting, and validating forward model configuration files,
restricted the use of forward models. As a result these hacks were unintetially restricted in version
[0.7.x] of everest-models (spinningjenny).

Forward models affected:

- Add templates
- Well constraints
- Schmerge

## Resolution

Each `op` dictionary object can have a optional `tokens` key, `tokens` refernce a sub-dictionary.
Keys `phase` and `rate` are moved from `op` into `tokens` and will be preserve to the same behavior.

#### Previously

```json hl_lines="9-10"
[
  {
    "drill_time": 27,
    "name": "INJECT1",
    "ops": [
      {
        "date": "2019-05-12",
        "opname": "rate"
        "phase": "WATER",
        "rate": 600.0
      }
    ]
  }
]
```

#### Now

```json hl_lines="9-12"
[
  {
    "drill_time": 27,
    "name": "INJECT1",
    "ops": [
      {
        "date": "2019-05-12",
        "opname": "rate"
        "tokens":{
          "phase": "WATER",
          "rate": 600.0
        }
      }
    ]
  }
]
```

Even though one is mark as [Previously](#previously) and the other [Now](#now),
both are still valid input files see [Schema](#schema) below

#### Schema

```yaml hl_lines="8-24"
---
arguments: -i/--input
fields:
- completion_date: {format: date, required: false, type: string}
  drill_time: {required: false, type: integer}
  name: {required: true, type: string}
  ops:
  - one of:
    - date: {format: date, required: true, type: string}
      opname: {required: true, type: string}
      template: {format: file-path, required: false, type: string}
      tokens:
         <string>: <any value>
         phase:
            choices: [WATER, GAS, OIL]
            required: false
            type: string
         rate: {required: false, type: number}
    - date: {format: date, required: true, type: string}
      opname: {required: true, type: string}
      phase:
         choices: [WATER, GAS, OIL]
         type: string
      rate: {required: false, type: number}
      template: {format: file-path, required: false, type: string}
  readydate: {format: date, required: false, type: string}
...
```

!!! note

    [Previously](#previously) will be depricated and removed in the future

These changes ware implemented in version [0.8.0].

###### More: Discussion/proposal [issue #358]

###### Next: Tokens [How-To Guides]

[0.7.x]: https://github.com/equinor/everest-models/releases/tag/0.7.4
[0.8.0]: https://github.com/equinor/everest-models/releases/tag/0.8.0
[issue #358]: https://github.com/equinor/everest-models/issues/358
[How-To Guides]: ../tokens/how_to_guide.md
