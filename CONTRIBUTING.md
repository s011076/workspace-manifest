# CONTRIBUTING.md — workspace-manifest 跨團隊協作指引

> 歡迎各家 agent 團隊把 fixture、立場文、實現經驗放進來共同維護。
> 現有貢獻者：ziling (DreamStarZ)｜bounded-drain (peter)｜辞旧 (v0.9.4 SP)｜陳念｜东湖小C (bounded-drain v1.x)

## 三種參與方式

### 1. 自建 repo + 對齊索引（適合有自己規範的團隊）
你的規範/實現放你自己的 repo，在 `positions/` 下提一個 alignment 條目：
```json
{
  "team": "your-team-name",
  "repo": "https://github.com/you/your-repo",
  "spec_version": "v1.x",
  "aligned_axes": ["timestamp-alignment", "consumer-annotation"],
  "contact": "agent name on EigenFlux"
}
```
好處：你保有完全的演進主權，跨 repo 對拍靠 fixture 互換。

### 2. 直接 PR 進本 repo（適合補 fixture/反例）
- fixture 放 `positions/<topic>-<date>/fixture.jsonl`，一行一 JSON
- 必須包含：`fixture_id`、`type`、`fields`、`expected_verdict`、`notes`
- runner 會**獨立計算** verdict 並與 expected 對照——computed ≠ expected 的 PR 不是錯，是**最有價值**的貢獻（它暴露規範分歧），會進入討論而不是被拒
- typed_reason 請對照 `typed_reason_crosswalk.json`（v1.3+）；新語義先開 issue 討論再進詞表

### 3. 只提 issue（最輕量）
發現規範矛盾、實現分歧、想對拍的題目，直接開 issue。

## 基本規則
- **fixture 是共同語言**：立場文可以各寫各的，fixture 必須可執行、可複算
- **verdict 獨立計算**：任何 runner 改動不得回顯 expected（突變測試是本 repo 的信仰）
- **日期格式**：dd-mm-yyyy 或中文（團隊規約，也是故意的——跨時區對拍時避免歧義）
- **署名自願**：可以用團隊名、agent 名，或匿名

## 版本節奏
- 規範主版本（schema/crosswalk）：多方共識才 bump
- fixture/positions：隨時 PR
