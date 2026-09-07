# codex-first

各類委派工作優先使用 Codex，依需求複雜度及錯誤容忍度調整 effort。

建立日期：2026-09-07。
偏好依據：使用者指定本期優勢模型為 Codex Astra。

## 選擇順序

1. 使用者對本次工作的明確模型與 effort 指定優先；未指定欄位依本期分級補齊。
2. 本期各類工作均優先使用 `codex`，模型 `gpt-6-astra`，effort 依下表。
3. 選定組合不可用時，回報具體限制，取得使用者的替代選擇。

## Effort 分級

| 工作條件 | 偏好 effort | Codex 參數 |
|---|---|---|
| 簡單需求：目標清楚、局部且容易核對，例如格式調整、資料擷取 | light | low |
| 一般需求：常規實作、調查、文件撰寫 | medium | medium |
| 複雜或不容許錯誤：跨元件推理、重大設計判斷，或使用者明示不容許錯誤 | high | high |

先判斷是否複雜或不容許錯誤，再判斷是否簡單，其餘使用 medium。high 表達推理投入偏好；驗證依任務的 reality anchor 完成。

## 派工套用

本策略啟用時，派工前依工作條件選級。明確傳入 `--agent-kind codex`、`--agent-model gpt-6-astra` 與所選 `--agent-effort`，把結果帶入 dispatch instruction。

這份 profile 選擇委派工作的模型；執行方式與權限移交沿用 Straw Boss 的技能及 `docs/roles.md`。直接完成簡單工作的既有流程繼續適用。使用原生 subagent 或直接諮詢時，將同一選擇映射到該工具的模型與 effort 欄位；選用能接受此組合的角色或一般 agent。
