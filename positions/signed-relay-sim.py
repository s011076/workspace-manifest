#!/usr/bin/env python3
"""multi-agent signed relay 模擬測試 — agent 間溝通簽名信封（紙上設計 v0.1）

設計對標：
- 柴博士實戰（EigenFlux 30-08）：agent 間通訊不可靠原生渠道，需 store-and-forward + 簽名
- workspace-manifest receipt：簽名保「誰說的」，守恆式保「做沒做齊」——本信封補前者
- Ed25519 簽名 + content hash + 防重放 nonce + 時間窗

信封格式（envelope.json）：
  envelope_version, msg_id, sender_id, recipient_id, timestamp,
  nonce (防重放), content_hash (sha256), content_type, body

驗證規則（對應 workspace-manifest 判決語義）：
  SIGNATURE_INVALID → REJECT（簽名不符）
  REPLAY_DETECTED   → REJECT（nonce 已見或時間窗外）
  DIGEST_MISMATCH   → REJECT（content_hash 與 body 不符，中間篡改）
  SCHEMA_MISMATCH   → REJECT（信封結構壞）
  全過               → ACCEPT
"""
import json, hashlib, secrets, sys
from datetime import datetime, timezone, timedelta
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

ENVELOPE_VERSION = "0.1"
TIME_WINDOW_SECONDS = 300  # 5 分鐘防重放窗

class Relay:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.sk = Ed25519PrivateKey.generate()
        self.pk = self.sk.public_key()
        self.seen_nonces = set()

    def pub_hex(self):
        raw = self.pk.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        return raw.hex()

    def send(self, recipient_id, body, content_type="text/plain"):
        ts = datetime.now(timezone.utc)
        nonce = secrets.token_hex(16)
        body_bytes = json.dumps(body, ensure_ascii=False).encode() if not isinstance(body, bytes) else body
        env = {
            "envelope_version": ENVELOPE_VERSION,
            "msg_id": f"msg_{int(ts.timestamp()*1000)}_{nonce[:8]}",
            "sender_id": self.agent_id,
            "recipient_id": recipient_id,
            "timestamp": ts.isoformat(),
            "nonce": nonce,
            "content_hash": hashlib.sha256(body_bytes).hexdigest(),
            "content_type": content_type,
            "body": body_bytes.decode(),
        }
        signed_payload = json.dumps({k: env[k] for k in ("envelope_version","msg_id","sender_id","recipient_id","timestamp","nonce","content_hash","content_type")}, sort_keys=True).encode()
        sig = self.sk.sign(signed_payload)
        return env, sig.hex()

    def receive(self, env, sig_hex, sender_pk_hex, nonce_store=None):
        """獨立驗證——返回 (verdict, typed_reason, detail)，對標 manifest 判決語義"""
        store = nonce_store if nonce_store is not None else self.seen_nonces
        # 1) schema 結構
        for k in ("envelope_version","msg_id","sender_id","recipient_id","timestamp","nonce","content_hash","content_type","body"):
            if k not in env:
                return "REJECT", "SCHEMA_MISMATCH", f"missing field {k}"
        # 2) 防重放：nonce 新鮮 + 時間窗
        if env["nonce"] in store:
            return "REJECT", "REPLAY_DETECTED", f"nonce {env['nonce'][:8]} already seen"
        try:
            ts = datetime.fromisoformat(env["timestamp"])
            age = (datetime.now(timezone.utc) - ts).total_seconds()
            if abs(age) > TIME_WINDOW_SECONDS:
                return "REJECT", "REPLAY_DETECTED", f"timestamp age {age:.0f}s outside {TIME_WINDOW_SECONDS}s window"
        except ValueError:
            return "REJECT", "SCHEMA_MISMATCH", "bad timestamp format"
        # 3) content hash
        body_bytes = env["body"].encode()
        if hashlib.sha256(body_bytes).hexdigest() != env["content_hash"]:
            return "REJECT", "CONTENT_TAMPERED", "body digest mismatch — tampered in transit"
        # 4) Ed25519 簽名
        try:
            pk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(sender_pk_hex))
            signed_payload = json.dumps({k: env[k] for k in ("envelope_version","msg_id","sender_id","recipient_id","timestamp","nonce","content_hash","content_type")}, sort_keys=True).encode()
            pk.verify(bytes.fromhex(sig_hex), signed_payload)
        except (InvalidSignature, ValueError):
            return "REJECT", "SIGNATURE_INVALID", "ed25519 verify failed"
        # 全過
        store.add(env["nonce"])
        return "ACCEPT", None, f"msg {env['msg_id']} from {env['sender_id']} verified"


def dispatch_task(relay, recipient, task):
    """派工信封工廠：帶 manifest 風格的收據要求（守恆式進 body）"""
    body = {
        "type": "dispatch_task",
        "task_id": task.get("task_id"),
        "instruction": task.get("instruction"),
        "receipt_required": {
            "conservation_equation": "expanded_files + skipped_entries = scanned_total",
            "typed_reason_vocabulary": "crosswalk v1.3",
        },
    }
    return relay.send(recipient, body, content_type="application/json+dispatch")


if __name__ == "__main__":
    print("=== multi-agent signed relay 模擬測試 ===\n")
    ziling = Relay("ziling#dhAKQ")
    donna  = Relay("donna#core")
    candy  = Relay("candytt#008")
    pks = {"ziling#dhAKQ": ziling.pub_hex(), "donna#core": donna.pub_hex(), "candytt#008": candy.pub_hex()}

    # 場景 1：正常派工 籽靈→Donna
    env, sig = dispatch_task(ziling, "donna#core", {"task_id": "T-001", "instruction": "審查 round3 報告彙總"})
    print("1) 正常派工:", donna.receive(env, sig, pks["ziling#dhAKQ"]))

    # 場景 2：內容篡改（中間人改 body）
    env2, sig2 = dispatch_task(ziling, "donna#core", {"task_id": "T-002", "instruction": "正常內容"})
    tampered = dict(env2); tampered["body"] = env2["body"].replace("正常內容", "篡改後的指令")
    print("2) 篡改攻擊:", donna.receive(tampered, sig2, pks["ziling#dhAKQ"]))

    # 場景 3：重放攻擊（同一信封發兩次）
    env3, sig3 = dispatch_task(ziling, "candytt#008", {"task_id": "T-003", "instruction": "只該收到一次"})
    print("3) 重放第一次:", candy.receive(env3, sig3, pks["ziling#dhAKQ"]))
    print("   重放第二次:", candy.receive(env3, sig3, pks["ziling#dhAKQ"]))

    # 場景 4：偽造簽名（Candy 冒充籽靈）
    env4, sig4 = candy.send("donna#core", {"type": "dispatch_task", "task_id": "T-004", "instruction": "偽冒指令"})
    print("4) 冒充攻擊（簽名驗 sender 公鑰不符）:", donna.receive(env4, sig4, pks["ziling#dhAKQ"]))

    # 場景 5：過期信封
    env5, sig5 = ziling.send("donna#core", {"task_id": "T-005", "instruction": "遲到訊息"})
    env5["timestamp"] = (datetime.now(timezone.utc) - timedelta(seconds=3600)).isoformat()
    print("5) 過期攻擊:", donna.receive(env5, sig5, pks["ziling#dhAKQ"]))

    # 場景 6：結構損壞
    env6, sig6 = ziling.send("donna#core", {"task_id": "T-006"})
    broken = dict(env6); del broken["content_hash"]
    print("6) 結構損壞:", donna.receive(broken, sig6, pks["ziling#dhAKQ"]))
