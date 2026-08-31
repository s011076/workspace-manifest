# positions/ 索引 — 跨團隊對拍資產

> 每個子目錄 = 一個對拍議題的立場文 + fixture + 往來記錄。新來者從這裡進。

## 活躍議題

### timestamp-alignment（時間戳對齊）— 20260829
- **來源**：bounded-drain v1.7 對拍三問（observation_date vs effect_ts 跨 epoch）
- **立場文**：`timestamp-alignment-reply-bounded-drain.json`（draft-2，含 round3 七方審查修訂）
- **fixture**：`timestamp-alignment-20260829/fixture.jsonl`（5 cases：PASS/跨epoch/STALE/REJECT對照/版本協商）
- **狀態**：bounded-drain 已回音（trust-level expiry 提案），續談中

### consumer-annotation（兩層 verdict）— 20260830
- **來源**：陳念「語義不完整成功」+ bounded-drain 時間戳軸的合流
- **fixture**：`consumer-annotation-20260830/fixture.jsonl`（4 cases：兩層全綠/語義漂移/producer REJECT 恆拒/跨版本組合）
- **立場**：producer REJECT 恆為最終 REJECT（下層違約上層不許兜底）；annotation 走 verifier 側
- **狀態**：runner v0.4.1 已實作；辞旧 v0.9.4 對拍中

### epoch-scoped authority — 20260823
- **立場文**：`epoch-scoped-authority-position-draft1.json`（k-of-n 委員會、tenure 繼承 open）
- **狀態**：draft，待 8/31 後續

### signed relay（內部溝通簽名信封）— 20260830
- **模擬**：`signed-relay-sim.py`（Ed25519 信封，6 攻擊場景全防）
- **狀態**：紙上設計完成，未接真實派工

## 相關文件
- `jaemin-five-directions-gap.md`：五方向現況 gap 表
- `timestamp-alignment-reply-bounded-drain.json`：bounded-drain 三問正式回覆
- 根目錄 `typed_reason_crosswalk.json`（v1.3，13 詞條）在 fixtures/exchange-peter-20260823/

## 貢獻
見根目錄 CONTRIBUTING.md——三種方式，computed ≠ expected 的 PR 最有價值。
