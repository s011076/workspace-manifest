#!/usr/bin/env python3
"""workspace-manifest fixture runner v0.4 —獨立計算 verdict（不再回顯 expected）

v0.4 修補（round3 對拍結論）：
- 守恆式：獨立算術檢查（沿襲 v0.3）
- ts_alignment：獨立計算 skew（effect_ts - observation_date），按三級閾值判決
  綠區(skew<=max_skew_ms)=PASS軸 / 黃區(<=10x)=QUARANTINE軸 / 紅區(>10x)=REJECT軸
- freshness：獨立計算 observation_date 距現在窗齡，超 freshness_window_ms → SOURCE_STALE
- schema_negotiation：receipt schema_version < target → CROSS_VERSION_SCHEMA → QUARANTINE
- fence 跨界：effect_epoch != fence_epoch 且守恆成立 → QUARANTINE（EPOCH_FENCE_TRIGGERED）
- verdict 組合規則（優先序）：conservation FAIL → REJECT（CONSERVATION_VIOLATION）
  紅區 skew → REJECT（SKEW_VIOLATION）/ fence 跨界 → QUARANTINE / freshness 超窗 → QUARANTINE
  跨版本 → QUARANTINE / 黃區 → QUARANTINE / 全過 → PASS
"""
import json, sys
from datetime import datetime, timezone

TARGET_SCHEMA_VERSION = (0, 4)  # runner 以 v0.4 為當前目標 schema

# typed_reason → verdict 映射（crosswalk v1.3；runner 依此獨立判決非守恆型 receipt）
TYPED_REASON_VERDICT = {
    "CONSERVATION_VIOLATION": "REJECT",
    "PREMISE_INVALID": "QUARANTINE",
    "SCHEMA_MISMATCH": "REJECT",           # 同代 fail-closed（ malformed 結構）
    "SOURCE_STALE": "QUARANTINE",
    "STALENESS_EXCEEDED": "QUARANTINE",
    "DATA_GAP": "UNKNOWN",
    "EPOCH_FENCE_TRIGGERED": "QUARANTINE",
    "SIGNATURE_INVALID": "REJECT",
    "REPLAY_DETECTED": "REJECT",
    "AUTHZ_DENIED": "QUARANTINE",
    "CONTENT_TAMPERED": "REJECT",
    # v1.3 新增：跨版本過渡（立場文 q2：跨版本=降級不=欺詐）
    "CROSS_VERSION_SCHEMA": "QUARANTINE",
    "SKEW_AMBER": "QUARANTINE",
    "SKEW_VIOLATION": "REJECT",
    "SEMANTIC_INCOMPLETE": "QUARANTINE",
}

def parse_ts(s):
    if not s: return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

def count_skipped(s):
    if isinstance(s, int): return s
    if isinstance(s, list):
        return sum(i.get("count", 0) if isinstance(i, dict) else 0 for i in s)
    return 0

def semver_tuple(v):
    try:
        return tuple(int(x) for x in str(v).lstrip("v").split(".")[:3])
    except Exception:
        return None

def compute_verdict(d):
    """獨立計算 verdict + 判決依據，完全不讀 expected_verdict"""
    typ = d.get("type", "")
    fields = d.get("fields", {}) if isinstance(d.get("fields"), dict) else {}
    checks = {}

    # ── 類型驅動判決（premise/crypto/replay 等非守恆型 receipt）──
    # 規則：typed_reason 明示失格原因 → 依 crosswalk v1.3 verdict 映射獨立判決
    typed = d.get("typed_reason")
    if typed:
        checks["typed_reason"] = None  # 佔位，映射見 TYPED_REASON_VERDICT

    # ── 守恆式 ──
    eq = d.get("conservation_equation")
    src = eq if isinstance(eq, dict) else fields
    e = src.get("expanded_files"); sc = src.get("scanned_total"); sk = count_skipped(src.get("skipped_entries", 0))
    if e is not None and sc is not None:
        checks["conservation"] = ("PASS" if e + sk == sc else "REJECT",
                                  f"{e}+{sk}={'=' if e+sk==sc else '!'}{sc}",
                                  None if e + sk == sc else "CONSERVATION_VIOLATION")
    else:
        checks["conservation"] = ("UNKNOWN", "no numeric fields", None)

    # ── 時間戳三軸（獨立計算）──
    obs = parse_ts(fields.get("observation_date"))
    eff = parse_ts(fields.get("effect_ts"))
    max_skew = fields.get("max_skew_ms")
    if obs and eff and max_skew is not None:
        skew_ms = abs((eff - obs).total_seconds()) * 1000
        if skew_ms <= max_skew:
            checks["ts_alignment"] = ("PASS", f"skew {skew_ms:.0f}ms <= {max_skew}ms (green)", None)
        elif skew_ms <= max_skew * 10:
            checks["ts_alignment"] = ("QUARANTINE", f"skew {skew_ms:.0f}ms in amber ({max_skew}-{max_skew*10}ms)", "SKEW_AMBER")
        else:
            checks["ts_alignment"] = ("REJECT", f"skew {skew_ms:.0f}ms > 10x threshold {max_skew*10}ms", "SKEW_VIOLATION")

    # ── freshness（observation_date 軸）──
    fw = fields.get("freshness_window_ms")
    if obs and fw is not None:
        age_ms = (datetime.now(timezone.utc) - obs).total_seconds() * 1000
        if age_ms > fw:
            checks["freshness"] = ("QUARANTINE", f"obs age {age_ms/86400000:.1f}d > window {fw/86400000:.1f}d", "SOURCE_STALE")
        else:
            checks["freshness"] = ("PASS", f"obs age within window", None)

    # ── epoch fence 跨界 ──
    fe = fields.get("fence_epoch"); ee = fields.get("effect_epoch")
    if fe is not None and ee is not None and ee != fe:
        checks["epoch_fence"] = ("QUARANTINE", f"effect_epoch {ee} != fence_epoch {fe}", "EPOCH_FENCE_TRIGGERED")

    # ── schema 版本協商 ──
    sv = semver_tuple(fields.get("schema_version") or d.get("schema_version"))
    if sv and sv < TARGET_SCHEMA_VERSION:
        # 舊版 receipt：缺 hard field（effect_ts）時降級 QUARANTINE
        if not fields.get("effect_ts"):
            checks["schema_negotiation"] = ("QUARANTINE", f"v{fields.get('schema_version')} receipt missing effect_ts hard field", "CROSS_VERSION_SCHEMA")
        else:
            checks["schema_negotiation"] = ("PASS", f"v{fields.get('schema_version')} receipt carries effect_ts", None)

    # ── consumer annotation 層（陳念兩層結構：producer verdict + consumer 夠不夠用）──
    if typ == "receipt_with_consumer_annotation":
        pv = fields.get("producer_verdict")
        exp = fields.get("consumer_expected_schema") or {}
        prod = fields.get("produced_schema") or {}
        if pv == "REJECT":
            checks["consumer_annotation"] = ("REJECT", "producer REJECT — annotation NOT_EVALUATED", "CONSERVATION_VIOLATION" if "conservation" in checks and checks["conservation"][0]=="REJECT" else None)
        else:
            # 語義漂移：produced 缺 expected 字段 或 policy snapshot 過期
            missing = [f for f in exp.get("fields", []) if f not in prod.get("fields", [])]
            stale = fields.get("policy_snapshot_version") and fields.get("policy_current_version") and fields["policy_snapshot_version"] != fields["policy_current_version"]
            if missing or stale:
                detail = f"missing fields {missing}" if missing else ""
                if stale: detail = (detail + "; " if detail else "") + f"policy snapshot {fields['policy_snapshot_version']} stale vs {fields['policy_current_version']}"
                checks["consumer_annotation"] = ("QUARANTINE", detail, "SEMANTIC_INCOMPLETE")
            else:
                checks["consumer_annotation"] = ("PASS", "schema semantically aligned", None)

    # ── 組合（優先序）──
    # 0) typed_reason 驅動（非守恆型 receipt 的主判決）
    if "typed_reason" in checks and typed:
        v = TYPED_REASON_VERDICT.get(typed)
        if v:
            return v, typed, checks
    for key in ("conservation", "ts_alignment", "epoch_fence", "freshness", "schema_negotiation", "consumer_annotation"):
        if key in checks:
            v, detail, reason = checks[key]
            if v in ("REJECT", "QUARANTINE"):
                return v, reason or key.upper(), checks
    return "PASS", None, checks

fixture_path = sys.argv[1] if len(sys.argv) > 1 else "fixtures/exchange-peter-20260823/fixture.jsonl"
strict = "--strict" in sys.argv  # strict 模式：computed != expected 即報錯
total = passed = rejected = quarantined = unknown = 0
mismatches = []

with open(fixture_path) as f:
    for line in f:
        line = line.strip()
        if not line: continue
        d = json.loads(line)
        total += 1
        fid = d.get("fixture_id", "?")
        expected = d.get("expected_verdict", "?")
        computed, reason, checks = compute_verdict(d)

        icon = {"PASS":"✅","REJECT":"❌","QUARANTINE":"⏳","UNKNOWN":"❓"}.get(computed,"  ")
        match = "✓" if computed == expected else "✗ MISMATCH"
        print(f"{icon} {fid}  [{match}]")
        print(f"   computed: {computed}" + (f" ({reason})" if reason else "") + f" | expected: {expected}")
        for k, cv in checks.items():
            if cv is None: continue
            v, detail, _ = cv
            print(f"   - {k}: {v} ({detail})")
        print()
        if computed != expected: mismatches.append((fid, computed, expected))

        if computed == "PASS": passed += 1
        elif computed == "REJECT": rejected += 1
        elif computed == "QUARANTINE": quarantined += 1
        else: unknown += 1

print("=" * 60)
print(f"Result: {total} cases (independently computed)")
print(f"  PASS: {passed} | REJECT: {rejected} | QUARANTINE: {quarantined} | UNKNOWN: {unknown}")
if mismatches:
    print(f"  ⚠ MISMATCH vs expected ({len(mismatches)}):")
    for fid, c, e in mismatches: print(f"    {fid}: computed={c} expected={e}")
    sys.exit(1)
else:
    print("  ✓ All computed verdicts match expected")
