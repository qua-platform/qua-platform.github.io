# Source of unified QM's documentation

[docs.quantum-machines.co](https://docs.quantum-machines.co)

To see it and develop it locally, ask NikolaQM to allow your GitHub account to
access a special dependency used for building docs (otherwise poetry install
below will fail), do

```
git clone --recurse-submodules https://github.com/qua-platform/qua-platform.github.io.git
```

and then do from `docs` directory (if this is the first time you are doing installation, please check Tips for install on Windows subsection below before continuing)

## Tips for install on Windows

1. install [Anaconda Python distribution](https://www.anaconda.com/products/distribution)
2. open anaconda terminal
3. do `pip install poetry`
4. do `conda install -c anaconda cairo`
5. go to documentation folder, and run

```
poetry install
cd docs
poetry run mkdocs serve
```

Your documentation will be seen in live preview mode (localhost:8000). Every
time changes are saved to the disk, rebuild of documentation will be triggered
during which (8-9s) site won't respond on clicks. After build site will
automatically reload.

### Troubleshooting

- if you have problem with git credentials (we use token auth) make sure you
setup credentials following this [guide](https://stackoverflow.com/questions/46878457/adding-git-credentials-on-windows).

## Typical workflow

1. Get up-to-date with everything `git pull --recurse-submodules`
2. Use `poetry run mkdocs serve` while editing
3. If editing docstrings in the submodules, commit changes there first. Work in subbranches and usual and open PR to main.

Check [MkDocs Material reference](https://squidfunk.github.io/mkdocs-material/reference/) to make use of various features available.

Person that releases new documentation should

1. Get up-to-date with everything `git pull --recurse-submodules`
4. (if config was changed) Build config documentation (see above)
5. Publish new version `poetry run mike deploy --push --update-aliases 0.1 latest ` 
6. Commit changes to main repository


## For documentation admin: publishing new version

To publish new version

```
poetry run mike deploy --push --update-aliases 0.1 latest 
```

To build config documentation (do once before publishing new version)
```
cd docs
cd qm-qua-sdk
poetry run poe generate-grpc
poetry run python ./docs/build_config_schema.py
```

### Troubleshooting

- If above command breaks due to missing packages go to submodule `/docs/docs/qm-qua-sdk` and do
`poetry install`.

## Transfer from .rst

These notes are for docs transfer from `.rst` format to new `.md` format.

Start with 
```
rst2myst convert *.rst 
docconvert --input rest --output google ./qm-qua-sdk/ --in-place
```

Change:

| from     |    to      |
|----------|------------|
| shields | requirement name + optional version like `{{ requirement("OPX+", "2.0.0") }}` or `{{ requirement("QUA", "0.3.3")`  or `{{ requirement("Octave") }}` |
| `:::{figure} dev_env1.png` | `![figure](dev_env1.png)` |
| `:::{note}` | `! Note` and indent note paragraph |
| `{ref} ...` links | standard markdown links `[test](url)` |
| ```{contents} :local: true``` | should be removed |
| `:label:` in equations (equation numbering)| remove for now from `.rst` before running automatic conversion to `.md`; then in `.md` use standard LaTeX `\label{eq:sample}` and refer to it as `$\eqref{eq:sample}$` in text |  
| ```:math:`E=mc^2` ``` | ```$E=mc^2$``` | 
|```Example::``` | ```Examples:``` (note plural; singular is admonition not code example) followed with indented section of ```>>> code```. *Alternative solution*: ```Example:``` followed with indented section of ```python <code in new lines>``` |
| ``` {func}`program <~qm.qua._dsl.program>` ``` | `[program][qm.qua._dsl.program]`  or `[qm.qua._dsl.program][]`|
| ```{eval-rst} .. csv-table::```| ```{{ read_csv('path_to_table.csv') }}```|
|``` {code}`a.b(2)` ```|  ``` `a.b(2)` ``` or with inline highlighting ``` `#!python a.b(2)` ``` |
| API references ```:func:`package.module.object` ``` |   `[some text][package.module.object]` or directly with "[package.module.object][]"|

For API references: To preserve underscore formatting use
```
[ `path._dsl.function_`][path._dsl.function_]
```

or **the best is to use** `{{f("path._dsl.function_")}}` macro 

Extra macros (python functions, and replacements) [can
be defined](https://mkdocs-macros-plugin.readthedocs.io/en/latest/macros/) in `/docs/macros.py`.
Currently used to provide `requirements` function.

For fine-tining docstring parsing, check [this](https://mkdocstrings.github.io/usage/)
and [this](https://mkdocstrings.github.io/griffe/docstrings/).

