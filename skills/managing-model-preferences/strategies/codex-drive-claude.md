# codex-drive-claude

由 Codex 主代理協調，Claude 執行輕量、一般與複雜工作；純文件工作使用 Codex low，以降低 token 消耗。

建立日期：2026-09-07。
偏好依據：使用者指定輕量工作給 Claude Sonnet、複雜工作給 Opus，只有文件使用 low effort 的 Codex，模式名稱為 `codex-drive-claude`。

## 選擇順序

1. 使用者對本次工作的明確模型與 effort 指定優先；未指定欄位依下表補齊。
2. 純文件撰寫、改寫、翻譯與排版使用 Codex `gpt-6-astra`，effort `low`，沿用原策略的 Codex 模型。
3. 其他工作先判斷是否複雜或不容許錯誤，使用 Claude `opus`、effort `high`；輕量工作使用 Claude `sonnet`、effort `low`；其餘一般工作使用 Claude `sonnet`、effort `medium`。
4. 同時包含程式變更與文件更新的工作，依程式工作的複雜度選擇 Claude。調查、查詢、審查及設計亦依 Claude 分級處理。
5. 選定組合不可用時，回報具體限制，由使用者選擇替代組合。

## 分級與派工參數

| 工作條件 | agent-kind | agent-model | agent-effort |
|---|---|---|---|
| 純文件工作 | codex | gpt-6-astra | low |
| 輕量：目標清楚、局部且容易核對 | claude | sonnet | low |
| 一般：常規實作、調查、查詢或審查 | claude | sonnet | medium |
| 複雜或不容許錯誤：跨元件推理、重大設計判斷，或使用者明示不容許錯誤 | claude | opus | high |

純文件工作即使篇幅長或推理較複雜，仍使用 Codex low；使用者明確覆寫時依指定執行。各類工作的驗證依其 reality anchor 完成。

## 套用

派工時明確傳入 `--agent-kind`、`--agent-model` 與 `--agent-effort`，將選定組合帶入 dispatch instruction。Claude CLI 支援 `sonnet`、`opus` 模型別名及 `low`、`medium`、`high` effort；Codex `gpt-6-astra` 與 `low` 依目前 harness 模型清單套用。

Codex 主代理負責分流、協調與結果整合。直接指示的簡單工作沿用主代理直接完成的流程；需要委派的執行工作依本策略選模。執行方式與權限移交依 Straw Boss 技能及 `docs/roles.md`。

使用原生 subagent 或直接諮詢時，將同一組合映射到工具的模型與 effort 欄位，選用支援該 provider 與組合的工具。新派工套用本策略，既有 dispatch instruction 維持原設定。切換 profile 更新後續選模規則；主會話模型由啟動設定決定。
