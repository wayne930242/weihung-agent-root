Status: approved
Approved at: 2026-09-25
Approved from: 使用者回覆「核准。不是改安裝，本來的腳本不要弄壞，而是讓腳本支援 full install/pi install 等等等」；第 1、2 項已依此修訂
Amended at: 2026-09-25；使用者改定 bridge 來源為上游 commit `227f5eb4450a070dfbc083a7fe75b8b35366b941`，原 1M tier 改用 Opus 5.5 1M

# 規格：完整遷移到 pi

決策依據見 [decision.md](decision.md)。

## 切換後可觀察的行為

1. **安裝目標**：`scripts/install.sh` 新增 `--target`，可重複指定，也可用逗號分隔，值為 `claude`、`codex`、`gemini`、`pi`、`full`。
   - `full` 等於前四者全部。
   - 不帶 `--target` 時，行為與現在完全相同（claude、codex、gemini），現有測試不需要修改就會通過。
   - `--target pi` 可以重複執行，每次都把以下內容安裝或更新到最新狀態：
     - pi 本體（npm 全域安裝）與 Herdr 的 pi integration。
     - 社群套件：`pi-claude-bridge` 固定上游 git commit `227f5eb4450a070dfbc083a7fe75b8b35366b941`（待 npm 版本包含 #120 才改回 npm）、`pi-herdr-agents`、`pi-mcp-adapter`，以及 design 階段選定的 ask／todo 套件。
     - aaaav，以本機路徑用 `pi install` 安裝。
     - `~/.pi/agent/AGENTS.md`：由 `CLAUDE.md` 與 `shared/*.md` 展開 `@import` 後產生。內容改寫成 pi 的用詞，不再提到 Claude Code 專屬工具名稱、`boss-say`、straw-boss、`/codex:rescue`。
     - user root 的 skill，放到 `~/.agents/skills`（Codex 目前也用這個位置，兩邊共用）。
     - `pi-mcp-adapter` 的 MCP 設定。
     - 依目前啟用的策略產生 `pi-herdr-agents` 設定，以及 pi 的預設 model 和 thinking。
2. **移除目標**：`scripts/uninstall.sh` 支援同樣的 `--target`，不帶時行為與現在相同。
   - `--target pi` 移除 pi 版安裝的設定與套件，但不動 pi 本體與登入狀態。
   - 切換流程就是 `install.sh --target pi`，再執行 `uninstall.sh --target claude,codex,gemini`。何時執行由使用者決定。Claude Code 的 binary 與登入保留，作為 bridge 的後端。
   - straw-boss 與 aaaav 的 Claude／Codex plugin 由各自的 repo 管理，不在本 repo 的腳本範圍內。
3. **開 session**：在 Herdr pane 裡、任何 repo 下啟動 pi，都能取得以下內容：
   - user 指令與所有 skill（user root 加上 aaaav）。
   - codebase-memory-mcp 等 MCP 工具。OAuth 型的 MCP server 授權一次後，之後都可以使用。
   - `claude-bridge/*` 與 `openai-codex/*` 兩組模型。
   - Herdr 狀態回報。
4. **派工**：主代理可以把工作派到另一個 app 的 cwd，開在看得見的 Herdr pane。
   - model 和 thinking 依啟用策略的 tier 設定選擇，某個 model 失敗時照 fallback 清單換下一個。
   - worker 一律 yolo。
   - 結果自動回送主代理，不需要輪詢。使用者可以進 pane 直接和 worker 對話。
5. **派工紀錄與接回**：主代理重啟後，可以列出還沒完成的 dispatch。worker 的 pane 重啟後，主代理可以接回它並繼續收結果。
6. **多主代理協調與交接**：
   - 同一台機器上的主代理可以互相找到對方、互傳訊息。
   - 一個工作範圍可以交接給新開的主代理 pane，新主代理會帶著交接內容與進行中的 dispatch 接手。
7. **shipping-task**：每個任務依目標 app 的慣例，走完 branch 或 worktree → commit → PR → merge。
8. **model profile**：
   - `managing-model-preferences` 切換策略時，把該策略的設定套用到 `pi-herdr-agents` 和 pi 預設 model。
   - Pi 的 tier 設定放在 JSON，沒有 agent kind 維度；策略檔保留 Claude Code／Codex 既有的 agent-kind、model、effort 表格、選擇順序與套用規則，並記錄 Pi tier 對照的理由。
9. **aaaav**：aaaav 的 skill 在 pi 裡可以使用。write／edit 工具執行後，由一個 pi extension 跑 `validate_tool_use` 的檢查，並把建議回饋給模型。

## 邊界情況

- Claude Code 登出，或 bridge 失敗：照策略的 fallback 清單改用 Codex 模型。
- 不在 Herdr 裡啟動 pi：`pi-herdr-agents` 不會啟用。主代理要說明派工暫時無法使用，不能改用別的方式偷偷派工。
- 同時安裝 `claude` 與 `pi` 時，經 bridge 呼叫的 Claude 會同時收到 pi 的指令和 `~/.claude/CLAUDE.md` 兩層。兩層內容同源，差別只在用詞，所以不會互相衝突；移除 `claude` 目標後就只剩 pi 那一層。

## 相容性與非目標

- 不設定任何 `anthropic/*` 模型，pi 不使用 Anthropic 訂閱 OAuth。
- 非目標：
  - coworker 二次審查流程。
  - 把 Claude Code 或 Codex CLI 當成派工對象。
  - 使用 omp。
  - 刪除 straw-boss repo（只是停止安裝）。

## 適用標準

- 本 repo 的 `AGENTS.md`：提示詞與 agent 指令用英文。
- git-safety 規則：只 stage 指定的檔案。
- 使用者全域指令中「簡單優先」與「外科手術式修改」兩節：社群套件已經涵蓋的功能不自己寫，自己寫的只有第 5 到 7 項，以及 aaaav 的 hook。

## Reality anchor

- **自動化**：擴充 `tests/install.sh`，在暫時的 `HOME` 裡跑一遍完整安裝與移除，斷言不帶 `--target` 時行為不變、各個目標的檔案結果，以及重複執行後結果不變。
- **Checkpoint**：自動化測試通過後，才在真正的 `HOME` 上執行切換。
- **真機驗證**：切換後在 Herdr 裡逐項實際操作第 3 到第 9 項，並記錄觀察到的輸出。
