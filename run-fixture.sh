#!/bin/bash
set -euo pipefail
FIXTURE="${1:-fixtures/exchange-peter-20260823/fixture.jsonl}"
[ ! -f "$FIXTURE" ] && echo "Usage: bash run-fixture.sh <fixture.jsonl>" && exit 1
python3 run_fixture.py "$FIXTURE"
