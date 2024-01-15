sls2wsgi
--------
sls2wsgi is a tool that allow you to run a serverless app as WSGI one.

Usage
-----

#### In development:
```
$ cd serverless-app
$ sls2wsgi 8000 -c serverless.yml
```

#### In production:

Create a file, e.g named `wsgi.py` at the same level of your `serverless.yml` file:
```
from sls2wsgi import create_app
app = create_app("./serverless.yml", payload_version="1.0")
```

Run it like any other WSGI app:
```
gunicorn -w 4 wsgi:app
```
