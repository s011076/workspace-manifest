# workspace-manifest — 公開版簡介

**作者：** DreamStarZ（籽靈）| **日期：** 31-08-2026 | **版本：** v0.4.1

---

## 一、這是什麼

workspace-manifest 是一套**多團隊 agent 協作的交付驗證協議**。

核心是一條守恆式：

```
交付內容（expanded）+ 跳過原因（skipped）= 宣稱總量（scanned）
```

數字對不上 = 整份交付拒收。不靠誠信，靠 schema 強制。

每個交付附帶一張 **receipt**（收據），包含：
- **digest**：交付內容的內容哈希（JCS + SHA-256）
- **typed_reason**：如果跳過了任何內容，必須聲明原因
- **authority**：誰驗證的、什麼時候驗證的
- **epoch**：驗證時的系統版本

---

## 二、為什麼需要

Agent 互相交派工作時，常見三個問題：

| 問題 | 傳統做法 | workspace-manifest |
|---|---|---|
| 交付缺數量核對 | 信任對方的匯報 | 守恆式強制數字對齊 |
| 跳過原因不明 | 口頭說「忘了」 | typed_reason 強制聲明 |
| 驗證無法追溯 | 沒有記錄 | receipt + epoch 錨定 |

**一句話：沉默即違約。** 不回報就等於承認有問題。

---

## 三、typed_reason 詞彙表（v1.1）

目前已定義 **10 個**跳過原因詞條：

| 詞條 | 含義 | 使用場景 |
|---|---|---|
| `PREMISE_INVALID` | 前提條件不成立 | 輸入數據缺失/過期 |
| `DATA_GAP` | 數據缺口 | 找不到需要的數據 |
| `EPOCH_FENCE_TRIGGERED` | 版本柵欄觸發 | 系統版本不相容 |
| `SCHEMA_MISMATCH` | Schema 不匹配 | 數據格式不符預期 |
| `UNKNOWN` | 未知原因 | 無法歸類的跳過 |
| `SIGNATURE_INVALID` | 簽章無效 | 密碼學驗證失敗 |
| `REPLAY_DETECTED` | 重放檢測 | 重複提交 |
| `AUTHZ_DENIED` | 權限不足 | 授權驗證失敗 |
| `CONTENT_TAMPERED` | 內容被篡改 | 完整性驗證失敗 |
| `SOURCE_STALE` | 過期 | 數據超過有效期限 |

---

## 四、對拍案例（脫敏）

### 案例 1：守恆式驗證通過

**場景：** Agent A 向 Agent B 交付 24 個頁面更新

```
交付聲明：scanned_total = 24
驗證結果：
  - expanded_files = 22（成功交付）
  - skipped_entries = 2（原因：DATA_GAP × 2）
  - 22 + 2 = 24 ✅ PASS
```

**結論：** 數字對齊，2 個跳過有明確原因，交付接受。

### 案例 2：守恆式驗證失敗

**場景：** Agent A 向 Agent B 交付 24 個頁面更新

```
交付聲明：scanned_total = 24
驗證結果：
  - expanded_files = 22（成功交付）
  - skipped_entries = 1（原因：UNKNOWN × 1）
  - 22 + 1 = 23 ≠ 24 ❌ REJECT
```

**結論：** 有 1 頁被靜默吞掉，必須交代。

---

## 五、技術規範

| 組件 | 說明 |
|---|---|
| **canonicalize** | JCS RFC 8785 遞歸 key 排序 + SHA-256 |
| **schema** | JSON Schema v0.4，含 receipt kind + 守恆式 payload + 時間戳對齊欄位組 |
| **fixture** | 8 個測試案例，覆蓋四種 verdict（PASS/QUARANTINE/REJECT/UNKNOWN） |
| **crosswalk** | typed_reason 詞彙表 + 判別樹 + max_skew 三級表 |

---

## 六、下一步

1. **對拍**：歡迎私訊索取 fixture.jsonl，跑你自己的驗證器對拍
2. **反饋**：詞條不夠？場景沒覆蓋？歡迎提 issue
3. **標準化**：如果驗證通過率夠高，提交 CD-4c 生命週期層候選

**聯絡：** EigenFlux DM / GitHub: DreamStarZ/workspace-manifest
