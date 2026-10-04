# Bad App

A tiny Flask app that logs an error while returning HTTP 200, so you can test
whether your observability tools catch failures that HTTP metrics miss.
Use it in a controlled test environment.

## Routes

| Route | Response | Purpose |
| --- | --- | --- |
| `/` | HTTP 200, `Hello World!` | Basic request |
| `/error` | HTTP 200, JSON error | Intentional error with a misleading status |
| `/healthz` | HTTP 200, `{"status":"ok"}` | Health probes |

## Quick Start

Requires Python 3.14.

```sh
python -m pip install pipenv==2026.2.2
pipenv verify
pipenv sync --dev
pipenv run serve
```

Open <http://localhost:5000/error> to trigger the demo failure.
Set `PORT` to change the port or `WEB_CONCURRENCY` to change the worker count
(default: two).

Run tests and the dependency audit:

```sh
pipenv run test
pipenv run pip-audit --strict
```

## Docker

```sh
docker build -t bad-app:local .
docker run --rm -p 5000:5000 bad-app:local
```

Check container behavior with `python3 scripts/smoke_container.py bad-app:local`.

## Helm

The chart is in [`charts/bad-app`](charts/bad-app). It defaults to a ClusterIP
service with ingress disabled. Pin a released image tag or digest for deployment.

```sh
helm lint --strict charts/bad-app
helm template bad-app charts/bad-app --set image.tag=RELEASE_TAG
```

Replace `RELEASE_TAG` with a published `sha-<full-commit>` tag.
See the [Maintainer Guide](docs/maintaining.md) for CI, releases, and deployment details.
