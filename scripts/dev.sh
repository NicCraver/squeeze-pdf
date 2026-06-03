#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
npm run build
source .venv/bin/activate
python -m client.app
