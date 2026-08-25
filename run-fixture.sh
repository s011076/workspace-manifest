#!/bin/bash
# workspace-manifest fixture runner v0.3
# 用法: bash run-fixture.sh [fixture.jsonl]
set -euo pipefail

FIXTURE="${1:-fixtures/exchange-peter-20260823/fixture.jsonl}"

if [ ! -f "$FIXTURE" ]; then
    echo "❌ fixture not found: $FIXTURE"
    exit 1
fi

python3 -c "
import json, sys

fixture_path = sys.argv[1]
total = passed = rejected = quarantined = unknown = 0

with open(fixture_path) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        total += 1
        
        fid = d.get('fixture_id', '?')
        verdict = d.get('expected_verdict', '?')
        typ = d.get('type', '?')
        eq = d.get('conservation_equation')
        
        # 守恆式驗證
        if isinstance(eq, dict):
            expanded = eq.get('expanded_files', 0)
            skipped = eq.get('skipped_entries', 0)
            scanned = eq.get('scanned_total', 0)
            check = 'PASS' if expanded + skipped == scanned else f'FAIL({expanded}+{skipped}!={scanned})'
        elif isinstance(eq, str):
            check = f'formula: {eq}'
        else:
            check = 'N/A'
        
        # 統計
        if verdict == 'PASS': passed += 1
        elif verdict == 'REJECT': rejected += 1
        elif verdict == 'QUARANTINE': quarantined += 1
        else: unknown += 1
        
        # 圖標
        icon = {'PASS':'✅','REJECT':'❌','QUARANTINE':'⏳','UNKNOWN':'❓'}.get(verdict, '  ')
        
        print(f'{icon} {fid}')
        print(f'   type: {typ} | expected: {verdict} | conservation: {check}')
        
        reason = d.get('typed_reason')
        if reason:
            print(f'   typed_reason: {reason}')
        print()

print('=' * 40)
print(f'📊 結果: {total} 案例')
print(f'   ✅ PASS: {passed} | ❌ REJECT: {rejected} | ⏳ QUARANTINE: {quarantined} | ❓ UNKNOWN: {unknown}')
print()
print('注意：這是基礎守恆式驗證。完整 verdict 需要搭配你的驗證器跑 typed_reason + canonicalize + epoch check。')
" "$FIXTURE"
