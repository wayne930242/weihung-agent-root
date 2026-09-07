# claude-only

例行派工全部留在 Claude。Opus xhigh 主協調，Fable 5.1 承接複雜功能與深入研究，Sonnet high 承接一般實作，Sonnet low 承接明確的小修改及查找整理。目標是在 Codex 額度不足時維持原有分層品質。

建立日期：2026-09-07。
偏好依據：使用者回報 Codex 額度即將用盡，要求依 `claude-drive-codex` 的分層改寫為 claude-only；使用者指定 Astra medium 那一層對標 Fable 5.1，並選擇原 Astra low 的一般實作改由 Sonnet high 承接。Fable 的 effort 由 Astra 分級平移為 medium，實測後可調整。

## 模型與 effort

| 角色或工作 | agent-kind | agent-model | agent-effort |
|---|---|---|---|
| 主協調：需求討論、分流、派工、追蹤及結果整合 | claude | opus | xhigh |
| 規格清楚、局部且容易驗證的小修改與機械工作 | claude | sonnet | low |
| 有明確目標的查找、資料整理、狀態檢查 | claude | sonnet | low |
| 一般實作、文件撰寫、常規分析及審查 | claude | sonnet | high |
| 複雜功能、深入研究、疑難診斷與重大設計判斷 | claude | fable | medium |

## 選擇順序

1. 使用者本次明確指定的模型與 effort 優先；未指定欄位依對應角色或工作補齊。
2. 主協調者使用 Opus xhigh。執行工作先判斷是否涉及複雜功能、深入研究或重大不確定性，符合時使用 Fable medium。
3. 規格清楚的小修改、機械工作、定向查找、整理與狀態檢查交給 Sonnet low。文件排版、格式轉換及資料摘錄屬此類；需要組織論點或撰寫完整內容的文件使用 Sonnet high。
4. 其餘一般實作、文件與分析使用 Sonnet high。不容許錯誤的工作以 Fable medium 執行，並依 reality anchor 驗證。
5. Sonnet low 工作若發現需要一般實作或進一步推理，帶著已取得的證據與未解問題轉交 Sonnet high；遇到複雜功能或深入研究則使用 Fable medium。Sonnet high 遇到具體難題時轉交 Fable medium。
6. 例行派工不使用 Codex。CLAUDE.md 明定需要跨模型視角的個案（UI/UX 設計精修、直接跨模型諮詢）先向使用者確認是否動用剩餘 Codex 額度；使用者不動用時由 Fable medium 執行，並在回報中標明未取得跨模型視角。
7. 選定組合不可用時回報具體限制，由使用者決定替代組合。

## 用量與協調

以完成合格工作的總消耗衡量成效，計入主協調、worker、交接、驗證與返工；本策略的消耗集中在 Claude 訂閱額度，觀察時一併記錄 Fable 與 Opus 的佔比。

直接指示的簡單工作沿用主代理直接完成的流程。需要委派時，以可獨立完成的完整工作為單位，提供目標、必要背景、檔案或證據位置與 reality anchor。獨立工作有明確並行收益時才增加 worker。

主協調者保留需求、決策、依賴及結果摘要；worker 負責其範圍內的調查、實作與驗證，回傳結果、證據位置及未解問題。主協調依事件追蹤並整合證據，出現矛盾或缺口時才進行針對性核對。生命週期與權限依 Straw Boss 的 `docs/roles.md`。

## 套用

派工明確傳入表中的 `--agent-kind`、`--agent-model` 與 `--agent-effort`，全部使用 `claude` kind。Claude CLI 的 `--model` 接受 `opus`、`sonnet`、`fable` 別名，Fable 5.1 全名為 `claude-fable-5-1`；`--effort` 接受 `low`、`medium`、`high`、`xhigh`、`max`，使用者所稱 x-high 對應實際參數 `xhigh`。

主協調會話啟動時使用 `claude --model opus --effort xhigh`；需要沿用既有 1M 上下文設定時使用 `--model 'opus[1m]'`。此 profile 定義選模規則，主會話模型及 effort 由啟動參數決定；既有會話的權限移交依 `handoff-orchestrator` 辦理，接手模型依本表的複雜工作組合或使用者當次指定。

原生 subagent 或諮詢工具依同一組合映射模型與 effort。新派工使用當前策略，既有 dispatch instruction 維持原設定。
