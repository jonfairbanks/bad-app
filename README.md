# Bad App

A Flask app for demonstrating misleading HTTP status codes in observability tools.
The `/error` route deliberately logs an exception and returns HTTP 200. This is
intentional demo behavior, covered by a regression test. Use this app only in a
controlled test environment.

| Route | Response | Purpose |
| --- | --- | --- |
| `/` | HTTP 200, `Hello World!` | Basic request |
| `/error` | HTTP 200, JSON error | Deliberately incorrect error status |
| `/healthz` | HTTP 200, `{"status":"ok"}` | Startup, readiness, and liveness |

The correct response for the demo exception would be
`return jsonify({"error": str(e)}), 500`. Keeping the broken route allows tests
of alerts that must detect error logs even when HTTP metrics look healthy.

## Local Development

Use Python 3.14 and Pipenv 2026.2.2. `Pipfile.lock` records exact dependencies
and their hashes; Pipenv remains the package manager.

```sh
python -m pip install pipenv==2026.2.2
pipenv verify
pipenv sync --dev
pipenv run test
pipenv run pip-audit --strict
pipenv run serve
```

Gunicorn binds to `0.0.0.0:5000`, writes request and error logs to standard
output/error, and handles SIGTERM. `PORT` changes the port; `WEB_CONCURRENCY`
changes the worker count (default: two). Workers get 20 seconds to finish active
requests. The Flask development server remains available with
`pipenv run python main.py`.

## Container

The multi-stage image uses a digest-pinned Python 3.14 Debian Trixie base.
Available Debian security updates are applied during builds, so OS packages
can advance independently of the pinned base digest.
Dependencies install from the lockfile with hash verification. The runtime
contains only application code and production dependencies, runs as UID/GID
10001, and excludes Pipenv, pip-audit, and pip.

```sh
docker build -t bad-app:local .
python3 scripts/smoke_container.py bad-app:local
```

The smoke test checks startup, all three routes, the image health command,
non-root identity, a read-only root filesystem, dropped capabilities, and clean
SIGTERM shutdown. Only `/tmp` needs writable storage for Gunicorn worker files.

## CI and Releases

PRs and pushes to `develop` and `main` run Python tests, a strict dependency
audit, AMD64 and ARM64 container smoke tests and vulnerability scans, Helm
validation, and a release-source check. Fixable high or critical image findings fail CI. A separate report includes
unfixed findings. This retains the existing unfixed-CVE policy while adding an
enforced gate; Debian packages are updated during the build.
External Actions use immutable commit SHAs. No Snyk token is configured, so the
security gates use pip-audit and Trivy without repository secrets.

Updates merge into `develop`. Only a same-repository `develop` PR may merge
into `main`. Configure both branches to require these observed CI contexts:

- `Release Source`
- `Python Tests`
- `Dependency Audit`
- `Container (amd64)`
- `Container (arm64)`
- `Helm Chart`

Dependabot checks Python dependencies, Docker base images, and Actions every
Monday at 9:00 AM Pacific. Its grouped patch/minor PRs target `develop` and use
policy-gated squash auto-merge. Major updates need manual review. The privileged
metadata workflow never checks out or executes PR code and never approves PRs.
Repository auto-merge is enabled, and both branches require the six CI checks
through an active ruleset without bypass actors. The workflows become active
on the default branch after the develop-to-main promotion.

Weekly promotion opens a direct `develop` to `main` PR and enables merge-commit
auto-merge after successful checks. It refuses to run without effective main
branch rules. Configure `RELEASE_TOKEN` as a fine-grained repository token with
Contents and Pull Requests write access. A separate token is needed because PRs
and merges created with `GITHUB_TOKEN` do not trigger downstream workflows.
The token is used only for GitHub API commands, without checking out PR code.
Promotion checks for source changes so a merge commit alone does not open a new
release PR. You can also open a `develop` to `main` PR manually.

A push to `main` publishes the existing Docker Hub image only after all CI gates
pass. It keeps version tags and `latest`, and adds `sha-<full-commit>` for GitOps.
The workflow pulls the published digest and smoke-tests it. Existing secrets
`DOCKER_USERNAME`, `DOCKER_ACCESS_TOKEN`, and `SLACK_WEBHOOK_URL` retain their
roles. Slack notifications stay within the existing release workflow.

## Helm Chart

The app owns `charts/bad-app`. Chart changes publish versioned OCI artifacts at
`oci://ghcr.io/jonfairbanks/charts/bad-app` after the image release succeeds.
Increment `Chart.yaml` for chart changes. Image-only releases do not republish
the chart. GHCR chart visibility may need to be set after the first publication;
private packages require registry credentials.

The chart defaults to a ClusterIP service on port 80 targeting port 5000,
with ingress disabled. It includes startup, readiness, and liveness probes on
`/healthz`, resource requests and a memory limit, rolling updates, a 30-second
termination grace period, no service-account token, a read-only filesystem,
dropped capabilities, RuntimeDefault seccomp, and a small writable `/tmp`.
The resource defaults are starting values; adjust them from actual usage.

```sh
helm lint --strict charts/bad-app
helm template bad-app charts/bad-app --set image.tag=sha-<released-commit>
```

For the eventual cluster rollout, add an Argo CD Application under
`cluster-state/applications/bad-app/`, use this OCI chart, and pin its version
and the published image digest. Keep exposure private and use the established
Vault-backed credential flow if the chart package is private. For example:

```yaml
image:
  repository: jonfairbanks/bad-app
  digest: sha256:<published-image-digest>
  pullPolicy: IfNotPresent
ingress:
  enabled: false
```

The default image tag is `latest` for discovery, not the cluster release pin.
Do not deploy the historical Docker Hub image before the corrected release is
published. Kubernetes deployment and Argo reconciliation are separate from
this repository preparation.
