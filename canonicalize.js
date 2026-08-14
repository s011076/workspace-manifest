const crypto = require("crypto");

function canonicalize(input) {
  if (input === null || typeof input !== "object") {
    throw new Error("Canonical form requires a JSON object");
  }
  if (Array.isArray(input)) {
    throw new Error("Wrap arrays as { items: [...] } before canonicalizing");
  }
  const json = JSON.stringify(input, Object.keys(input).sort());
  return Buffer.from(json, "utf8");
}

function sha256Hex(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function bindingDigest(record) {
  const scope = {
    slot_id: record.slot_id,
    predicate_id: record.predicate_id,
    pre_state: record.pre_state,
    operation: record.operation,
    post_state: record.post_state,
    expected_verdict: record.expected_verdict
  };
  return sha256Hex(canonicalize(scope));
}

function frontierPositionHash(snapshot) {
  return sha256Hex(canonicalize({
    frontier_hash: snapshot.frontier_hash,
    position: snapshot.position,
    snapshot_ts: snapshot.snapshot_ts
  }));
}

module.exports = { canonicalize, sha256Hex, bindingDigest, frontierPositionHash };
