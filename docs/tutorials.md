## Installation

```bash
pip install git+{GH_TOKEN}@https://github.com/equinor/spinningjenny.git
```

## Local Test

Make sure you have access and permission to the Equinor github organization.
clone the project to your local repository.

```bash
git clone https://github.com/equinor/spinningjenny.git
```

> It is a good idea to create an SSH key and authorize it as an Equinor Single sign-on (SSO) key

Install test dependencies

```bash
pip install .[test]
# pip install -e .[test] # if editable is desire
# pip install .\[test\] # zsh
```

Run tests
```bash
pytest -sv
```

## Docs

Install documentation dependencies

```bash
pip install .[docs]
# pip install -e .[docs] # if editable is desire
# pip install .\[docs\] # zsh
```

If missing, autogenerate forward model jobs reference documentation resources

```bash
docs/reference/load_jobs_metadata.py
```

Start Documentation Server

```bash hl_lines="6"
mkdocs serve
INFO     -  Building documentation...
INFO     -  Cleaning site directory
INFO     -  Documentation built in 1.94 seconds
INFO     -  [20:45:25] Watching paths for changes: 'docs', 'mkdocs.yml'
INFO     -  [20:45:25] Serving on http://127.0.0.1:8000/
```
Head to the given address (localhost:port)