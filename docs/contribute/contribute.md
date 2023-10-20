## How to Introduce a New Forward Model Job

### Operation Remover

Operation Remover is a small and simple forward model job that will be used for this demonstration.

Operation Remover has the following criteria:

- I/O elements are wells.json and well name list
- remove well operations from wells.json where well names intersect.
- If no operation present **do nothing**

We will try as much as possible to adhere the existing [Project Structure](../explanation.md#project-structure)

```bash
# From project root
mkdir src/everest_models/jobs/fm_ops_remover
cd src/everest_models/jobs/fm_ops_remover
touch __init__.py __main__.py tasks.py parser.py cli.py
cd -
```
#### Parser
Lets first implement the interface between us and the user. what we expect to get from the user.

> It is recommended to look to the shared module for reusable code instead of (re)writing schemas and parser from scratch

More function protected/private functions can be present within this module, in order to increase readability or code logic, but the only function that we care for and must be exposed is `build_argument_parser`.


```python hl_lines="8"
{!> contribute/fm_ops_remover/parser.py!}
```

#### Tasks

It can be argued that `tasks.py` is small enough that it can be moved to `cli.py` and removed. But for demonstration purposes we will have a small `tasks.py`.

```python
{!> contribute/fm_ops_remover/tasks.py [ln:1-6,13-]!}
```

#### CLI

CLI, command line interface, is our forward model job main entry point to the rest of the job's functionality. Thus all other relevant job functionality should be referenced within this module's `main_entry_point` function.
This function is what is going to be exposed to `Everest-models` plugin.

`main_entry_point` includes:

- parse user input
- post parse logic
- core functionality
- closing logic (output)

```python hl_lines="5"
{!> contribute/fm_ops_remover/cli.py!}
```

#### Dunder Modules

Expose main_entry_point 

```python
{!> contribute/fm_ops_remover/__init__.py!}
```

make `main_entry_point` function the main entry point if module is referenced as a script

```python
{!> contribute/fm_ops_remover/__main__.py!}
```

#### Plugin Executable

Add forward model job to `forward_models`. This directory is package as data files, 
thus files is what is being executed by everest, or whomever is using `everest-models` plugin.

> The name of the `forward_models`' file should be the same as the job excluding the `fm_` prefix

```bash
echo EXECUTABLE fm_ops_remover > src/everest_models/forward_models/ops_remover
```

#### Standalone Script

Optional, but a plus, add job as a project script under `pyproject.toml`

```toml hl_lines="4"
# pyproject.toml
...
[project.scripts]
fm_ops_remover = "everest_models.jobs.fm_ops_remover.cli:main_entry_point"
...
```

Then you are able to run the job from the terminal as follow.

```bash
> ops_remover --help
usage: ops_remover [-h] [--lint] [--schemas] -i INPUT -o OUTPUT -w WELLS [WELLS ...]

Given everest generated wells.json file and a list of well names. remove the intersecting names' operations.

optional arguments:
  -h, --help            show this help message and exit
  --lint                Lints all given input (file) arguments with no data transformation.
  --schemas             Output all file schemas that are taken as input parameters.

required named arguments:
  -i INPUT, --input INPUT
                        Everest generated wells.json file
  -o OUTPUT, --output OUTPUT
                        Output File
  -w WELLS [WELLS ...], --wells WELLS [WELLS ...]
                        wells to modified.
```

## Documentation

### User Documentation

Everest-models user documentation is build by [Everest](https://github.com/equinor/everest), As such it should be created, and modified over on that end. Please look to [Everest Tutorial](https://github.com/equinor/everest/tree/main/docs/source/tutorial)
directory to know more of where your forward model documentation should live.

### Dev Documentation

Developer documentation lives here, in the `everest-models` project, Make sure **exposed** core function(s) have **docstring(s)**.

```python hl_lines="7-12"
{!> contribute/fm_ops_remover/tasks.py!}
```
Build documentation resources, there are expects of the codebase that is valuable for the developers, but cannot be referenced directly. Such as the parser help menu and the job schemas, these components are constantly changing and to prevent mismatch between codebase and documentation we build the documentation resource files prior to running the `mkdocs serve`

```bash
docs/reference/load_jobs_metadata.py
```

Once you've build the documentation resources, you can add them to the reference page as follow.

> ignore `\` it is there, so not to execute the code snippet within

```markdown hl_lines="5 8"
<!--docs/reference/ops_remover/reference.md-->

```bash
\{!> reference/ops_remover/help!}
```\
```yaml
\{!> reference/ops_remover/schema.yml!}
```\

## Tasks
::: everest_models.jobs.fm_ops_remover.tasks

<!--If you have custom models specific to the job-->
## Models
$pydanic: everest_models.jobs.fm_ops_remover.<module>
```

```yaml hl_lines="9"
# mkdocs.yml

...
nav:
  ...
  - Reference:
    - jobs:
      # Please put it in alphabetical order
      - Operation Remover: reference/ops_remover/reference.md
      ...
```

last thing to do is to start documentation sever and see if all has been loaded correctly

```bash
mkdocs serve
```