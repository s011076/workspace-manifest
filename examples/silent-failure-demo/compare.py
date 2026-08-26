#!/usr/bin/env python3
"""The Cost of Silence — 10-line comparison

Runs both scenarios and shows the difference.
Usage: python3 compare.py
"""
import json
from pathlib import Path

here = Path(__file__).parent

print("=" * 60)
print("SCENARIO A: Traditional chat-message delivery (no manifest)")
print("=" * 60)
log = (here / "01-without-manifest.log").read_text()
# The report says "all done" — but reality:
print('Report says:      "Done! Updated all the pages, everything looks good 👍"')
print("Reality:          18/24 pages OK, 6 skipped SILENTLY, 1 CORRUPTED")
print("Consumer knows:   NOTHING until students complain")
print("Diagnosis time:   3 hours + blame cycle")
print()

print("=" * 60)
print("SCENARIO B: Same delivery WITH workspace-manifest receipt")
print("=" * 60)
receipt = json.loads((here / "02-with-manifest-receipt.json").read_text())
eq = receipt["conservation_equation"]
expanded = eq["expanded_files"]
skipped = eq["skipped_entries"]
total = eq["scanned_total"]

print(f"Receipt declares: {expanded} delivered + {sum(s['count'] for s in skipped)} skipped = {total} total")
for s in skipped:
    print(f'  SKIP [{s["reason"]:16s}] x{s["count"]}: {s["evidence"]}')
balance_ok = expanded + sum(s['count'] for s in skipped) == total
print(f"Conservation:     {'✅ BALANCED' if balance_ok else '❌ VIOLATION — REJECT'}")
print("Consumer knows:   EVERYTHING, before publishing. Can fetch the 6 missing pages or publish with eyes open.")
print()

print("=" * 60)
print("THE DIFFERENCE")
print("=" * 60)
print("Same task. Same 24 pages. Same agent capabilities.")
print("The ONLY difference: one enforced conservation + typed reasons.")
print()
print("Silence is not neutrality. Silence is where failures hide.")
