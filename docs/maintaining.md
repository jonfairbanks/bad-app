# Maintainer Guide

## Runtime and Container

Dependencies come from `Pipfile.lock` with hash verification. Gunicorn listens
on `0.0.0.0:5000`, logs to stdout/stderr, and gives active requests 20 seconds
to finish after SIGTERM. For the Flask development server, run
`pipenv run python main.py`.

The multi-stage image uses a digest-pinned Python 3.14 Debian Trixie base and
applies available Debian updates during builds. It runs as UID/GID 10001 and
excludes Pipenv, pip-audit, and pip. Only `/tmp` needs writable storage.

```sh
python3 scripts/smoke_container.py bad-app:local
```

The smoke test checks all routes, container health, non-root identity, a
read-only root filesystem, dropped capabilities, and SIGTERM shutdown.
The `/error` response deliberately remains HTTP 200; a regression test preserves
this behavior.

## CI and Branch Rules

Changes go through `develop`. Only a same-repository PR from `develop` may
merge into `main`. Require these checks on both branches:

- `Release Source`
- `Python Tests`
- `Dependency Audit`
- `Container (amd64)`
- `Container (arm64)`
- `Helm Chart`

CI runs tests, pip-audit, container smoke tests, Trivy scans, and Helm validation.
Fixable high or critical image vulnerabilities fail CI; a separate report
includes unfixed findings. External Actions are pinned to commit SHAs.

Dependabot checks Python dependencies, Docker base images, and Actions every
Monday at 9:00 AM Pacific. Grouped patch/minor PRs target `develop` and use
squash auto-merge gated by branch rules. Major updates need manual review.
The privileged metadata workflow never checks out or executes PR code.

## Releases

Weekly promotion opens a `develop` to `main` PR when source files differ,
checks for effective main branch protections, and enables merge-commit
auto-merge after required checks pass. You can also open the promotion PR manually.

Configure these repository secrets:

| Secret | Purpose |
| --- | --- |
| `PERSONAL_TOKEN` | Fine-grained token with Contents and Pull Requests write access for promotion |
| `DOCKER_USERNAME` | Docker Hub username |
| `DOCKER_ACCESS_TOKEN` | Docker Hub publishing token |
| `SLACK_WEBHOOK_URL` | Release notifications |

Promotion uses `PERSONAL_TOKEN` for GitHub API commands so the PR and merge
trigger downstream workflows.

After all CI gates pass, a push to `main` publishes `jonfairbanks/bad-app`
with version tags, `latest`, and `sha-<full-commit>`. The release workflow pulls
the published digest and smoke-tests it.

## Helm and GitOps

Increment `charts/bad-app/Chart.yaml` when changing the chart. After the image
release succeeds, chart changes publish a versioned OCI artifact at
`oci://ghcr.io/jonfairbanks/charts/bad-app`. Image-only releases skip chart
publication. Check GHCR visibility after first publication; private packages
require registry credentials.

The chart exposes service port 80 to container port 5000, probes `/healthz`,
and uses a read-only filesystem with writable `/tmp`, dropped capabilities,
RuntimeDefault seccomp, and no service-account token. Tune resource defaults
from actual usage.

Manage cluster rollout through an Argo CD Application in
`cluster-state/applications/bad-app/`. Pin the OCI chart version and published
image digest, keep exposure private, and use Vault-backed registry credentials
for private packages. Example values:

```yaml
image:
  repository: jonfairbanks/bad-app
  digest: sha256:<published-image-digest>
  pullPolicy: IfNotPresent
ingress:
  enabled: false
```

The chart's default `latest` tag is for discovery. Use a release pin for cluster
deployments.
