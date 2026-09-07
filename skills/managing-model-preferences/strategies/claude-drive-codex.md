# claude-drive-codex

Opus xhigh 主協調，Astra 負責一般實作與深入研究，Sonnet 承接明確的小修改及查找整理。目標是在品質足夠的前提下降低兩家合計用量，並由 Claude 分攤工作。

建立日期：2026-09-07。
偏好依據：使用者實測 Astra low 足以完成一般實作與協調，medium 適合複雜功能與深入研究；使用者選擇 Opus xhigh 主協調，並指定 Sonnet 承接規格清楚、容易驗證的小修改、機械工作、查找、整理及狀態檢查。

## 模型與 effort

| 角色或工作 | agent-kind | agent-model | agent-effort |
|---|---|---|---|
| 主協調：需求討論、分流、派工、追蹤及結果整合 | claude | opus | xhigh |
| 規格清楚、局部且容易驗證的小修改與機械工作 | claude | sonnet | low |
| 有明確目標的查找、資料整理、狀態檢查 | claude | sonnet | low |
| 一般實作、文件撰寫、常規分析及審查 | codex | gpt-6-astra | low |
| 複雜功能、深入研究、疑難診斷與重大設計判斷 | codex | gpt-6-astra | medium |

## 選擇順序

1. 使用者本次明確指定的模型與 effort 優先；未指定欄位依對應角色或工作補齊。
2. 主協調者使用 Opus xhigh。執行工作先判斷是否涉及複雜功能、深入研究或重大不確定性，符合時使用 Astra medium。
3. 規格清楚的小修改、機械工作、定向查找、整理與狀態檢查交給 Sonnet low。文件排版、格式轉換及資料摘錄屬此類；需要組織論點或撰寫完整內容的文件使用 Astra low。
4. 其餘一般實作、文件與分析使用 Astra low。不容許錯誤的工作以 Astra medium 執行，並依 reality anchor 驗證。
5. Sonnet 工作若發現需要一般實作或進一步推理，帶著已取得的證據與未解問題轉交 Astra low；遇到複雜功能或深入研究則使用 Astra medium。Astra low 遇到具體難題時升至 medium。
6. Fable 5.1 保留為使用者明確指定的個案選項；effort 依該次指定確認。選定組合不可用時回報具體限制，由使用者決定替代組合。

## 用量與協調

以完成合格工作的總消耗衡量成效，計入主協調、worker、交接、驗證與返工；分別觀察 token、實際費用及訂閱額度。

直接指示的簡單工作沿用主代理直接完成的流程。需要委派時，以可獨立完成的完整工作為單位，提供目標、必要背景、檔案或證據位置與 reality anchor。獨立工作有明確並行收益時才增加 worker。

主協調者保留需求、決策、依賴及結果摘要；worker 負責其範圍內的調查、實作與驗證，回傳結果、證據位置及未解問題。主協調依事件追蹤並整合證據，出現矛盾或缺口時才進行針對性核對。生命週期與權限依 Straw Boss 的 `docs/roles.md`。

## 套用

派工明確傳入表中的 `--agent-kind`、`--agent-model` 與 `--agent-effort`。Claude CLI 支援 `opus`、`sonnet` 別名及 `low`、`xhigh` effort；使用者所稱 x-high 對應實際參數 `xhigh`。Astra 的 `gpt-6-astra`、`low` 與 `medium` 依目前 harness 模型清單套用。

主協調會話啟動時使用 `claude --model opus --effort xhigh`；需要沿用既有 1M 上下文設定時使用 `--model 'opus[1m]'`。此 profile 定義選模規則，主會話模型及 effort 由啟動參數決定；既有會話的權限移交依 `handoff-orchestrator` 辦理。

原生 subagent 或諮詢工具依同一組合映射 provider、模型與 effort，選擇能接受此組合的工具或角色。新派工使用當前策略，既有 dispatch instruction 維持原設定。
