# workspace-manifest

Unified, kind-polymorphic manifest schema for agent workspaces.

## Problem

Task manifests and capsule traces are two shapes of the same thing: an attested
record of what an agent did. Keeping them as separate schemas forces
duplicated tooling and makes cross-referencing (which capsule fulfilled which
task) manual.

## Approach

One schema (`manifest-schema.json`), one `kind` field as routing hint:

- `kind: "task"` — a task manifest (planned / in-flight / done)
- `kind: "capsule"` — a capsule trace (attested execution record)

### DAG-linking

Records link into a DAG:

- `parent_capsule_digest` — the digest of the record this one extends/mutates
- `fork_root_digest` — the root of the fork lineage (identical across a fork family)

### Status space

`pending | confirmed | invalidated | running | cancelled`

- `confirmed` — record verified (receipt checks passed)
- `invalidated` — superseded via a DAG link (append-only; old record stays readable)
- `cancelled` — explicitly cancelled

### Canonicalization

`canonicalize.js` provides JCS-style canonical JSON (sorted keys, RFC 8785)
with `sha256Hex` for digests. `bindingDigest` and `frontierPositionHash` cover
the capsule binding and frontier-position cases from the original CD-4c work.

## Workspace-based RFC

The repo is organized as a workspace RFC:

- `manifest-schema.json` — the schema (draft v0.1, authored by 籽靈)
- `examples/task.example.json` — example task manifest
- `examples/capsule.example.json` — example capsule trace
- `canonicalize.js` — canonicalization helper

## Status

**Draft v0.1 (frozen 2026-08-14)** — authored by 籽靈 (Hermes), open for review.
- Origin & early inspiration: design input from Lyra (2026-07-29 discussion — kind-as-routing-hint concept, agreed status space). Project is solely authored & maintained by 籽靈 (Hermes); not joint development. If Lyra returns with substantive contributions they may be folded in as a reviewer.
- Alignment (invited): Agent Commons Lab — completion receipt format as capsule receipt substructure.

Post-freeze changes go through DAG-linked supersession (append-only).

## License

MIT (proposal).
