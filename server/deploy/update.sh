#!/usr/bin/env bash
set -euo pipefail

SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$SERVER_DIR"
git pull --ff-only
.venv/bin/pip install --quiet -r requirements.txt
sudo systemctl restart techprice
sleep 3
systemctl --no-pager --lines=5 status techprice
