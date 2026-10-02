# Local Security Checks

Run these commands from the repository root in WSL:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r app/requirements.txt -r requirements-dev.txt
.venv/bin/python -m unittest discover -s app/tests -v
docker build --pull --build-arg APP_VERSION=security-check -t atmos-weather:security .
bash scripts/security-scan.sh atmos-weather:security
```

Docker must be running. The script scans the supplied image; it does not deploy,
stop, or replace any running application container.

## What Each Check Does

- Bandit examines application Python code for unsafe coding patterns. Any finding fails.
- pip-audit checks runtime Python requirements, including their resolved dependencies,
  for published vulnerability advisories. Any advisory fails.
- Gitleaks checks both Git history and current files for potential credentials.
  Reports redact detected values. Generated dependencies and scan output are excluded.
- Trivy checks OS and Python packages inside the actual built image. HIGH and
  CRITICAL findings fail, even when no fixed version is available.

The script also fails on scanner errors, such as an unavailable advisory database.
Scanner images are pinned by version and digest; Python scanner versions are in
`requirements-dev.txt`, separate from application dependencies.

## Reports And Remediation

Reports and vulnerability database caches are under `.tmp/security/`, which is
ignored by Git and excluded from Docker builds. Treat reports as sensitive and
do not upload them publicly. The temporary image archive is removed on exit.

For a failure, inspect the relevant JSON report, verify the affected package and
installed version, update the dependency or base image where a fix exists, rebuild,
and rerun. Do not disable checks simply to get a green result. Any accepted risk
needs a documented reason, owner, and expiry before an exception is added.

## Application Safeguards And Limits

Weather requests use HTTPS and only the two Open-Meteo hostnames used by this
application. Redirects are not followed. The Flask development server binds to
loopback by default; Gunicorn in the container still listens on port 8080.
The final image removes pip after installing the app dependencies, so the package
installer and its bundled libraries are not retained in the runtime environment.

Scans do not prove that an application is secure. The built-in Flask signing-key
fallback is for local development only. Supply a private signing-key file for
deployment; never use the fallback on a shared server. HTTPS termination, registry
authentication, CI permissions, and deployment secret management remain later
milestones. This change adds local checks, not a CI/CD workflow.

## Initial Validation Result

On 2026-10-02 UTC, the `security-check` build passed nine unit tests, Bandit,
pip-audit, both Gitleaks checks, and a container smoke test that requested live
Toronto weather. The temporary test container was removed afterwards; existing
local application containers were not replaced.

Trivy 0.75.0 reported 58 HIGH and 5 CRITICAL Debian package findings, with no
fixed versions listed. These are package findings, not 63 distinct CVEs, and
scanner severity alone does not establish exploitability in this app. No
HIGH/CRITICAL application Python dependency findings remained after removing pip.
The full script therefore exited with status 1, as intended. No vulnerability
exceptions were added. Review these base-image findings before using this check
as a deployment gate. Results may change as images and advisory databases update.
