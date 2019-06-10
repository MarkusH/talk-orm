# talk-orm

This demo uses Python 3.7 and Django 2.2

## Setup

```bash
$ python3.7 -m venv .venv
$ ./.venv/bin/pip install -r requirements.txt
$ ./.venv/bin/python manage.py migrate
$ ./.venv/bin/python manage.py loaddata goodreads
```

## Development

If the virtual environment `.venv` doesn't exist yet, create one:

```bash
$ python3.7 -m venv .venv
```

Afterwards, ensure all dependencies are installed:

```bash
$ ./.venv/bin/pip install -r requirements-dev.txt
```

The code is formatted using [black](https://pypi.org/project/black/).

```bash
$ ./.venv/bin/black .
```
