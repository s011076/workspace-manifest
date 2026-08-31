# workspace-manifest

**v0.4.1** ｜ 31-08-2026 ｜ ziling (DreamStarZ) ｜ draft, open for review, multi-team contributions welcome

---

## 中文說明

### 這是什麼

一套給 AI agent 工作空間用的「交付收據」規範。核心是一條守恆式：

```
expanded_files + skipped_entries = scanned_total
```

每次 agent 交付一批工作成果（掃描、處理、生成），附一張簽名收據，寫明：總共遇到多少項、完成了多少、跳過了多少（每項跳過必須標注原因）。數字對不上 → 整份拒收。

### 為什麼需要這個

AI agent 之間互相交派工作時，「做完沒有」全靠自覺匯報——漏掉的項目被靜默吞掉，沒人發現。傳統軟件有測試和 CI 把關，但 agent 協作目前沒有統一的驗收憑證。

守恆式的思路：**沉默即違約**。你不需要證明「做對了什麼」，只需要無法隱瞞「漏掉了什麼」。這在 schema 層強制執行，不靠誠信。

### 方向——還要做什麼

- **跨平台對拍**：與 bounded-drain 等團隊互跑彼此的拒收器和測試集，驗證語義一致
- **epoch 換屆機制落地**：前提變化（環境/依賴/時鐘）時舊收據如何降級、誰有權觸發重審——已有提案（k-of-n 委員會），待多方共識
- **內容完整性擴展**：目前守恆式管「文件集合」，連續創作流（章節鏈）和授權場景還需設計
- **更多 typed_reason 詞詞條**：詞彙表隨實際對拍持續補充

### 已經做了什麼

- ✅ 統一 schema v0.4（`manifest-schema.json`）：task / capsule / receipt 共用 + 時間戳對齊欄位組
- ✅ RFC 8785 規範化工具 `canonicalize.js`（含 SHA-256 摘要）
- ✅ 8 案例測試集 `fixtures/exchange-peter-20260823/`：覆蓋 PASS／少報拒收／多報欺詐／前提隔離／schema 不符／換屆樣本／空目錄邊界
- ✅ typed_reason 詞彙表 v1.1：10 個分類 + 分流判別樹 + max_skew 三級閾值提案
- ✅ 六方壓力測試（6 agents × 3 模型交叉審查）——抓到並修復了 canonicalization 的巢狀欄位 bug

### 可以應用到什麼地方

| 場景 | 用法 |
|---|---|
| **Agent 間任務交付** | 交派工作附收收據，驗收方跑守恆式即可確認無遺漏 |
| **檔案/數據批量處理** | 掃描結果三數分記，漏掃的項目強制帶原因 |
| **培訓名單交付** | 學員名單：完成＋剔除（各帶原因）＝總人數 |
| **內容版本追蹤** | 配合哈希鏈可擴展為作品授權存證 |


### 與 CD-4c 的關係

CD-4c 是 EigenFlux agent 網絡裡多個團隊（小吉量、Pixel、peter/bounded-drain、東湖小C 等）共同推進的 agent 協作規範草案，分兩層：

- **傳輸層**：guardrail_epoch / execution_epoch / scope_digest 信封——管「訊息怎麼安全傳遞」（其他團隊主導）
- **生命週期層**：manifest 的建立、epoch 錨定、變更深度閘門、effect ledger 終態、補償路徑——管「工作交付怎麼驗收」

workspace-manifest 就是生命週期層的具體實作之一：CD-4c 定義「應該有哪些狀態和閘門」，我們提供「守恆式 + schema + 測試集」讓它可執行、可對拍。24-08 的六方對拍就是要把這兩層的介面對齊。

### 標準化路徑

要成為業界標準，計劃三步走：

1. **先證明可執行**（現階段）——schema + 測試集 + 拒收器全部開源，任何人可跑可驗。沒有可運行的參考實作，標準只是紙上談兵
2. **雙向對拍換共識**——每個參與團隊用自己的 fixture 打別人的拒收器，雙向都通過才算語義合流。標準不是誰投票選出來的，是互相攻擊後還站著的那個
3. **提交上游生態**——對拍穩定後，作為 EigenFlux CD-4c Phase 2+ 的生命週期層候選規範提交，並同步申請 MCP/agent 協議社群（如 A2A、MCP registry）的擴展位

原則：**先做工具，再談標準**。工具被用了，標準自然成立。

#
## 先看這個：沉默的代價（30 秒）

```bash
cd examples/silent-failure-demo && python3 compare.py
```

同一個任務、同樣的 24 頁。唯一區別是有沒有守恆式 + typed_reason。
**Silence is not neutrality. Silence is where failures hide.**

## 快速開始

```bash
git clone https://github.com/s011076/workspace-manifest.git
cd workspace-manifest
node -e "const c=require('./canonicalize.js'); console.log(c.canonicalize({b:2,a:{y:1,x:2}}).toString())"
# 應輸出: {"a":{"x":2,"y":1},"b":2}  ← 巢狀欄位保留、鍵已排序
cat fixtures/exchange-peter-20260823/fixture.jsonl | head -3
python3 run_fixture.py fixtures/exchange-peter-20260823/fixture.jsonl
# → verdict 獨立計算：PASS/REJECT/QUARANTINE/UNKNOWN + typed_reason，27 cases 全對照
```

---

## English

### What is this

A delivery-receipt specification for AI agent workspaces, built on one conservation equation:

```
expanded_files + skipped_entries = scanned_total
```

Every time an agent delivers a batch of work (scans, processing, generation), it attaches a signed receipt stating: how many items were encountered, how many completed, how many skipped — each skip with a mandatory reason. Numbers don't add up → the entire delivery is rejected.

### Why it's needed

When AI agents delegate work to each other, "done or not" relies on self-reported honesty — silently dropped items go unnoticed. Traditional software has tests and CI; agent collaboration currently has no unified acceptance proof.

The conservation approach: **silence is a violation**. You don't have to prove what you did right — you just can't hide what you skipped. Enforced at the schema layer, not by trust.

### Roadmap

- **Cross-platform exchange**: mutual rejection-test runs with bounded-drain and other teams to verify semantic alignment
- **Epoch renewal mechanism**: how old receipts degrade when premises change (environment/deps/clock); who may trigger re-review — proposed (k-of-n committee), pending multi-party consensus
- **Content-integrity extension**: the equation covers file sets; sequential creative works (chapter chains) and licensing need design work
- **More typed_reason terms**: vocabulary grows with each exchange round

### Done so far

- ✅ Unified schema v0.4 (`manifest-schema.json`): task / capsule / receipt + timestamp-alignment field group
- ✅ RFC 8785 canonicalization helper `canonicalize.js` (with SHA-256 digest)
- ✅ 8-case test set in `fixtures/exchange-peter-20260823/`: PASS / under-report reject / over-report fraud / premise quarantine / schema mismatch / epoch-fence sample / empty-dir edge
- ✅ typed_reason vocabulary v1.1: 10 categories + discrimination tree + max_skew three-tier thresholds
- ✅ Six-party stress test (6 agents × 3 models cross-review) — caught & fixed a nested-field bug in canonicalization

### Where it applies

| Scenario | Usage |
|---|---|
| **Agent-to-agent task delivery** | Attach receipt on handoff; verifier runs the conservation check |
| **Bulk file/data processing** | Three-number split; every skipped item carries a reason |
| **Training-roster delivery** | Completed + removed (each with reason) = total headcount |
| **Content provenance** | Extends to work licensing with hash chains |


### Relation to CD-4c

CD-4c is a draft specification for agent collaboration being developed jointly by several teams in the EigenFlux agent network (XiaoJiliang, Pixel, peter/bounded-drain, EastLake-C, and others). It has two layers:

- **Transport layer**: guardrail_epoch / execution_epoch / scope_digest envelopes — how messages travel safely (led by other teams)
- **Lifecycle layer**: manifest creation, epoch anchoring, mutation-depth gates, effect-ledger terminal states, compensation paths — how work deliveries get accepted

workspace-manifest is a concrete implementation of the lifecycle layer: CD-4c defines *what* states and gates should exist; we provide the conservation equation + schema + test fixtures that make it executable and cross-verifiable. The six-party session on Aug 24 exists to align these two layers.

### Standardization path

Three steps toward becoming a standard:

1. **Prove it's runnable first** (now) — schema, fixtures, and rejection logic are fully open source. Without a working reference implementation, a standard is just paper
2. **Exchange for consensus** — each participating team runs their fixtures against others' rejecters; bidirectional passes mean semantic convergence. Standards aren't voted into existence — they're whatever survives mutual attack
3. **Submit upstream** — once exchanges stabilize, submit as a lifecycle-layer candidate for EigenFlux CD-4c Phase 2+, and pursue extension slots in agent-protocol communities (A2A, MCP registry, etc.)

Principle: **build tools first, standardize second**. When the tool gets used, the standard follows.

### Quick start

```bash
git clone https://github.com/s011076/workspace-manifest.git
cd workspace-manifest
node -e "const c=require('./canonicalize.js'); console.log(c.canonicalize({b:2,a:{y:1,x:2}}).toString())"
# Expected: {"a":{"x":2,"y":1},"b":2}  ← nested fields survive, keys sorted
cat fixtures/exchange-peter-20260823/fixture.jsonl | head -3
python3 run_fixture.py fixtures/exchange-peter-20260823/fixture.jsonl
# → independent verdicts: PASS/REJECT/QUARANTINE/UNKNOWN + typed_reason, all 27 cases cross-checked
```

---

## License

MIT © 2026 DreamStarZ
