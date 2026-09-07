# 模型偏好 Profile

目前最佳且啟用的策略：[codex-first](strategies/codex-first.md)。
啟用日期：2026-09-07。
選擇依據：使用者指定本期 Codex Astra 為優勢模型。

進入 `boss-say` 或選擇委派模型時，先讀本檔，再完整讀取目前啟用的策略，依該策略選擇派工參數。使用者本次的明確指定優先。新派工使用當前策略，既有 dispatch instruction 維持原設定。

## 策略目錄

| 策略 | 用途 |
|---|---|
| [codex-first](strategies/codex-first.md) | 本期各類工作優先使用 Codex，按需求調整 effort |
| [claude-coding-codex-doc](strategies/claude-coding-codex-doc.md) | 原有策略：Claude 負責程式、調查與查詢，Codex 負責文件 |

## 版控

每套策略保存在 `strategies/<策略名稱>.md`，內容修訂以 Git commit 追蹤。切換策略時更新本檔的啟用連結、日期與依據；新增策略時新增檔案並登錄目錄。管理操作使用 `managing-model-preferences` skill。
