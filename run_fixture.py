#!/usr/bin/env python3
"""workspace-manifest fixture runner v0.3 —真正執行守恆式驗證"""
import json, sys

fixture_path = sys.argv[1] if len(sys.argv) > 1 else "fixtures/exchange-peter-20260823/fixture.jsonl"
total = passed = rejected = quarantined = unknown = 0
errors = []

with open(fixture_path) as f:
    for line in f:
        line = line.strip()
        if not line: continue
        d = json.loads(line)
        total += 1
        fid = d.get("fixture_id", "?")
        verdict = d.get("expected_verdict", "?")
        typ = d.get("type", "?")
        eq = d.get("conservation_equation")

        def count_skipped(s):
            """skipped_entries 可能是 int 或 list"""
            if isinstance(s, int): return s
            if isinstance(s, list): return sum(item.get("count", 0) if isinstance(item, dict) else 0 for item in s)
            return 0

        cr = "N/A"
        if isinstance(eq, dict):
            e = eq.get("expanded_files", 0)
            s = count_skipped(eq.get("skipped_entries", 0))
            sc = eq.get("scanned_total", 0)
            if e + s == sc:
                cr = f"PASS ({e}+{s}={sc})"
            else:
                cr = f"FAIL ({e}+{s}={e+s}!={sc})"
                errors.append(fid)
        elif isinstance(eq, str):
            fields = d.get("fields", {})
            if isinstance(fields, dict):
                e = fields.get("expanded_files", 0)
                s = count_skipped(fields.get("skipped_entries", 0))
                sc = fields.get("scanned_total", 0)
                if sc > 0:
                    if e + s == sc:
                        cr = f"PASS ({e}+{s}={sc})"
                    else:
                        cr = f"FAIL ({e}+{s}={e+s}!={sc})"
                        errors.append(fid)
                else:
                    cr = f"FORMULA: {eq} (no numeric values)"
            else:
                cr = f"FORMULA: {eq}"

        reason = d.get("typed_reason")
        icon = {"PASS":"✅","REJECT":"❌","QUARANTINE":"⏳","UNKNOWN":"❓"}.get(verdict,"  ")
        print(f"{icon} {fid}")
        print(f"   type: {typ} | expected: {verdict}")
        print(f"   conservation: {cr}")
        if reason: print(f"   typed_reason: {reason}")
        print()

        if verdict == "PASS": passed += 1
        elif verdict == "REJECT": rejected += 1
        elif verdict == "QUARANTINE": quarantined += 1
        else: unknown += 1

print("=" * 50)
print(f"Result: {total} cases")
print(f"  PASS: {passed} | REJECT: {rejected} | QUARANTINE: {quarantined} | UNKNOWN: {unknown}")
if errors:
    print(f"  Conservation FAIL: {', '.join(errors)}")
else:
    print("  All conservation checks passed")
