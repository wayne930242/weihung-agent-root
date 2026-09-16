# claude-only

例行派工全部留在 Claude。Opus xhigh 主協調，Sonnet low 承接明確的小修改及查找整理，Sonnet high 承接一般實作與文件，Opus 1M low 承接 UI/UX 審查及指示清楚的複雜工作，Fable 5.1 high 承接指示不清的複雜工作。目標是在不動用 Codex 與 Antigravity 額度的前提下，維持與 drive-all 相同的分層品質。

建立日期：2026-09-07。
更新日期：2026-09-16。
偏好依據：使用者回報 Codex 額度即將用盡，要求依 `claude-drive-codex` 的分層改寫為 claude-only，並選擇原 Astra low 的一般實作改由 Sonnet high 承接。2026-09-16 使用者要求補齊到與 drive-all 同等級：複雜層依 `claude-with-agy` 的對映拆成 Opus 1M low（指示清楚）與 Fable 5.1 high（指示不清），複雜度改用環境不可預測性判定，UI/UX 獨立成列並取消動用 Codex 額度的詢問分支。

## 模型與 effort

| 角色或工作 | agent-kind | agent-model | agent-effort |
|---|---|---|---|
| 主協調：需求討論、分流、派工、追蹤及結果整合 | claude | opus | xhigh |
| 規格清楚、局部且容易驗證的小修改與機械工作 | claude | sonnet | low |
| 有明確目標的查找、資料整理、狀態檢查 | claude | sonnet | low |
| 一般實作、重構、多檔修改、文件撰寫、常規分析及審查，以及可預測環境中的大量程式碼工作 | claude | sonnet | high |
| UI/UX 設計審查、視覺稽核與例行檢視 | claude | opus[1m] | low |
| 複雜工作且指示清楚：環境不可預測 | claude | opus[1m] | low |
| 複雜工作且指示不清：環境不可預測且指示或情境模糊 | claude | claude-fable-5-1 | high |

## 選擇順序

1. 使用者本次明確指定的模型與 effort 優先；未指定欄位依對應角色或工作補齊。
2. 主協調者使用 Opus xhigh。
3. 複雜度以環境不可預測性判定：外部系統、執行期狀態或資料的行為超出工作可預先掌握的範圍，必須邊探測邊調整才能推進時才算複雜。程式碼量、檔案數、跨元件修改與驗證嚴格度本身不構成複雜。
4. 複雜工作中，指示不清且情境模糊者使用 Fable 5.1 high，其餘使用 Opus 1M low，並依該工作的 reality anchor 核對選擇。
5. 其餘工作依類別選擇：
   - Sonnet low：規格清楚的小修改、機械工作、定向查找、資料整理與狀態檢查。文件排版、格式轉換及資料摘錄屬此類。
   - Sonnet high：一般實作、重構、多檔修改、需要組織論點或撰寫完整內容的文件、常規分析及審查，以及可預測環境中的大量程式碼工作。
   - Opus 1M low：UI/UX 設計審查、視覺稽核與例行檢視。
6. 混合工作依主要交付物所屬類別選擇。Sonnet low 工作若發現需要一般實作或進一步推理，帶著已取得的證據與未解問題轉交 Sonnet high；證據顯示環境不可預測時轉交 Opus 1M low，指示同時模糊時轉交 Fable 5.1 high。
7. CLAUDE.md 指派給 Codex 的個案（UI/UX 設計精修、直接跨模型諮詢）依本表對應列路由，並沿用該規則要求的傳輸方式。本策略不派工給 Codex，回報時標明未取得跨模型視角。
8. 選定組合不可用時回報具體限制，由使用者決定替代組合。

## 用量與協調

以完成合格工作的總消耗衡量成效，計入主協調、worker、交接、驗證與返工；本策略的消耗集中在 Claude 訂閱額度，觀察時一併記錄 Opus 與 Fable 的佔比。

直接指示的簡單工作沿用主代理直接完成的流程。需要委派時，以可獨立完成的完整工作為單位，提供目標、必要背景、檔案或證據位置與 reality anchor。獨立工作有明確並行收益時才增加 worker。

主協調者保留需求、決策、依賴及結果摘要；worker 負責其範圍內的調查、實作與驗證，回傳結果、證據位置及未解問題。主協調依事件追蹤並整合證據，出現矛盾或缺口時才進行針對性核對。生命週期與權限依 Straw Boss 的 `docs/roles.md`。

## 套用

派工明確傳入表中的 `--agent-kind`、`--agent-model` 與 `--agent-effort`，全部使用 `claude` kind。Claude CLI 的 `--model` 接受 `opus`、`sonnet`、`fable` 別名，1M 上下文使用 `'opus[1m]'`，Fable 5.1 全名為 `claude-fable-5-1`；`--effort` 接受 `low`、`medium`、`high`、`xhigh`、`max`，使用者所稱 x-high 對應實際參數 `xhigh`。

主協調會話啟動時使用 `claude --model opus --effort xhigh`；需要沿用既有 1M 上下文設定時使用 `--model 'opus[1m]'`。此 profile 定義選模規則，主會話模型及 effort 由啟動參數決定；既有會話的權限移交依 `handoff-orchestrator` 辦理，接手模型依本表的複雜工作組合或使用者當次指定。

原生 subagent 或諮詢工具依同一組合映射模型與 effort。新派工使用當前策略，既有 dispatch instruction 維持原設定。
