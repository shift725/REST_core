#!/usr/bin/env sh
set -e

: "${DB_HOST:?DB_HOST must be set}"

echo "[entrypoint] waiting for database ${DB_HOST}:${DB_PORT:-5432} (max 60s)..."
python - <<'PY'
import os, socket, sys, time

host = os.environ['DB_HOST']
port = int(os.environ.get('DB_PORT', '5432'))
deadline = time.time() + 60
last_err = None
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"[entrypoint] database reachable at {host}:{port}")
            sys.exit(0)
    except OSError as exc:
        last_err = exc
        time.sleep(1)
print(f"[entrypoint] timed out waiting for {host}:{port}: {last_err}", file=sys.stderr)
sys.exit(1)
PY

echo "[entrypoint] applying migrations..."
python manage.py migrate --noinput

echo "[entrypoint] collecting static files..."
python manage.py collectstatic --noinput

echo "[entrypoint] ensuring admin superuser..."
python manage.py ensure_superuser

echo "[entrypoint] launching: $*"
exec "$@"
