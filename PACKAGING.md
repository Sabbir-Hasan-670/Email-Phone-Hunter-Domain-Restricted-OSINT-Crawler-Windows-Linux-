# Packaging Guide (Email/Phone Hunter)

This guide turns your existing script into an installable **Python package** that works across multiple Python versions and exposes a `email-hunter` command.

## Folder layout

```
your-project/
├─ README.md                  # your main readme
├─ pyproject.toml             # build & metadata
└─ src/
   └─ email_hunter/
      ├─ __init__.py
      ├─ cli.py               # wrapper calling main()
      └─ app.py               # your existing script (rename/move here)
```

> Put your current **`email_hunter.py`** code into `src/email_hunter/app.py`. Make sure it defines `def main():` and has the `if __name__ == "__main__": ...` guard (optional when packaged).

## Install (editable) for development

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .\.venv\Scripts\activate
pip install -U pip build
pip install -e .[pdf]    # add [pdf] if you want PDF parsing
```

Now you can run the CLI from anywhere:

```bash
email-hunter --help
```

## Build wheels (for all users)

```bash
pip install build
python -m build    # creates dist/*.whl and dist/*.tar.gz
```

Install the wheel:

```bash
pip install dist/email_phone_hunter-0.1.0-py3-none-any.whl[pdf]
```

Or recommend **pipx** so users keep it isolated and easy to run:

```bash
pip install -U pipx
pipx install .
# then:
email-hunter --help
```

## Test against multiple Python versions

Use **tox** so you know it works across 3.8–3.12.

`tox.ini`:

```ini
[tox]
envlist = py38,py39,py310,py311,py312
isolated_build = true

[testenv]
deps = pytest
commands = pytest -q
```

Run:
```bash
pip install tox
tox
```

## Notes

- Optional extra `pdf` pulls in `pdfminer.six` for PDF parsing.
- The console entry point is defined in `pyproject.toml` under `[project.scripts]`:  
  `email-hunter = "email_hunter.cli:main"`
- If you also want a **requirements.txt**, generate it from the metadata or create:
  ```
  requests>=2.28
  beautifulsoup4>=4.11
  pdfminer.six>=20221105  # optional
  ```
