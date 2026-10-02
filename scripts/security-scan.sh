#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
IMAGE="${1:-atmos-weather:security}"
PYTHON_BIN="${PYTHON_BIN:-$REPO_ROOT/.venv/bin/python}"
REPORT_DIR="$REPO_ROOT/.tmp/security"
GITLEAKS_IMAGE="ghcr.io/gitleaks/gitleaks:v8.30.1@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f"
TRIVY_IMAGE="aquasec/trivy:0.75.0@sha256:af6acf9a6b85dfe389a1941505c0ce9efef52a4719635e1a962f022a3d855daa"

command -v docker >/dev/null
"$PYTHON_BIN" -m bandit --version >/dev/null
"$PYTHON_BIN" -m pip_audit --version >/dev/null
docker image inspect "$IMAGE" >/dev/null
mkdir -p "$REPORT_DIR/cache"
chmod 700 "$REPORT_DIR"
FAILED=0

# Run every check, but preserve any failure in the final exit status.
check() {
    local name="$1"
    shift
    printf '\nChecking %s...\n' "$name"
    if "$@"; then
        printf 'PASS: %s\n' "$name"
    else
        printf 'FAIL: %s (finding or scanner error)\n' "$name" >&2
        FAILED=1
    fi
}

check "Python code (all severities)" "$PYTHON_BIN" -m bandit -r app -x app/tests \
    -f json -o "$REPORT_DIR/bandit.json"
check "Python runtime dependencies (all known advisories)" "$PYTHON_BIN" -m pip_audit \
    -r app/requirements.txt -f json -o "$REPORT_DIR/pip-audit.json"
check "Secrets in Git history" docker run --rm \
    -v "$REPO_ROOT:/repo:ro" -v "$REPORT_DIR:/reports" "$GITLEAKS_IMAGE" git /repo \
    --config /repo/.gitleaks.toml --redact --report-format json \
    --report-path /reports/gitleaks-history.json
check "Secrets in current files" docker run --rm \
    -v "$REPO_ROOT:/repo:ro" -v "$REPORT_DIR:/reports" "$GITLEAKS_IMAGE" dir /repo \
    --config /repo/.gitleaks.toml --redact --report-format json \
    --report-path /reports/gitleaks-files.json

# Export the app image so the scanner never needs access to the Docker socket.
docker image save --output "$REPORT_DIR/image.tar" "$IMAGE"
trap 'rm -f -- "$REPORT_DIR/image.tar"' EXIT
check "Container HIGH/CRITICAL vulnerabilities (including unfixed)" docker run --rm \
    -v "$REPORT_DIR:/scan" "$TRIVY_IMAGE" image --input /scan/image.tar \
    --cache-dir /scan/cache --scanners vuln --severity HIGH,CRITICAL --exit-code 1 \
    --format json --output /scan/trivy.json

printf '\nReports: %s\n' "$REPORT_DIR"
exit "$FAILED"
