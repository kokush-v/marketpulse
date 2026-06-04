#!/bin/sh

set -eu

echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] cron-entrypoint: starting MarketPulse cron container"

exec python -m app.features.background_jobs.cron_runtime
