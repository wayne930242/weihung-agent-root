# 完整遷移到 pi 系 harness

把目前以 Claude Code 與 Codex 為主的工作環境，整體遷移到 pi 或 oh-my-pi（omp）。範圍涵蓋 user root（本 repo 與其安裝腳本）、straw-boss、aaaav。straw-boss 與 aaaav 若無法完整對接，改在本 repo 重寫，連同 harness 的安裝腳本一起納入。

## 實測事實（2026-09-25，omp 18.3.1、pi 0.87.1、Herdr integration omp v10／pi v9）

| 項目 | omp | pi |
|---|---|---|
| 讀取 Claude plugin 內的 skill（straw-boss、aaaav 等） | 可以，需開 `enabledProviders`，共 55 個 skill，名稱不帶 plugin 前綴 | 不行；只讀 `~/.agents/skills`、`~/.pi/agent/skills`，plugin 要打包成 pi package |
| 展開 `CLAUDE.md` 的 `@import` | 可以 | 不行；只讀 `~/.pi/agent/AGENTS.md` 或 `CLAUDE.md` |
| skill 內文的 `${CLAUDE_PLUGIN_ROOT}` | bash 中為空值 | 同樣為空值 |
| MCP | 內建，自動匯入 Claude 設定；OAuth 型 HTTP server 回 401，需重新授權 | 需另裝 `pi-mcp-adapter` |
| `pi-claude-bridge`（經 Agent SDK 使用 Claude 訂閱） | 載入失敗：缺 `formatSkillsForPrompt` export | 可用，`claude-bridge/claude-opus-5-5` 正常回應 |
| `pi-herdsman` | 載入失敗：缺 `contentText` export | 安裝成功 |
| `pi-herdr-agents` | 安裝成功，但子 agent 固定以 `pi` 啟動（`launch.ts:613`） | 實測可在 Herdr pane 派子 agent 到其他 repo 的 cwd，結果自動回送父 agent |
| Herdr 取得 session identity | integration 已安裝，未實測 | 可以，取得 session 檔路徑 |
| 內建 subagent、ask、todo、plan、`modelRoles` | 有 | 需套件補足 |

## 外部事實

- Anthropic 條款將訂閱 OAuth 限定於 Claude Code 與原生應用程式，並保留不預告執行的權利：<https://code.claude.com/docs/en/legal-and-compliance>。社群回報伺服器端已開始封鎖（未取得一手證據）。
- 經 Agent SDK 的第三方 app 使用訂閱額度，是官方明列的用途：<https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan>。
- 經 bridge 呼叫的 Claude Code 會自行載入 `~/.claude/CLAUDE.md`，與 pi 自己的指令檔形成兩層。

## 套件原始碼確認（2026-09-25）

| 需求 | 套件 | 結論 |
|---|---|---|
| MCP | `pi-mcp-adapter` 2.37.0 | 支援 stdio、遠端 HTTP 的完整 OAuth 流程（PKCE，token 存在 OS credential store）。設定檔在 `~/.pi/agent/mcp.json`，也會讀 `~/.agents/mcp.json`、`.mcp.json`。不會自動匯入 Claude Code 的設定：要執行 `/mcp setup`，或把 `hostConfigDiscovery` 打開（預設是 off）。 |
| 主代理之間傳訊 | `pi-intercom` 0.14.0 | 透過本機 broker socket 互相發現；工具叫 `intercom`；收到訊息會自動觸發一輪對話，不需要輪詢；`list` 會顯示 cwd、model 與 Herdr pane。和 `pi-herdr-agents` 沒有名稱衝突。交接的完整流程要自己寫。 |
| 問使用者 | `pi-ask-user` 0.15.1 | 工具叫 `ask_user`；每次呼叫只能問一題，支援多選與自由輸入。 |
| todo | `@capdiem/pi-todo` 0.3.2 | 工具叫 `todo`，有即時 widget；resume 後能不能保留狀態，原始碼是 minified，目前只有 README 的說法。 |
| plan mode | `@signalridge/pi-plan-mode` 1.4.1 | 真正的唯讀受限模式；和 `pi-herdr-agents` 都註冊 `/plan`，會衝突。後者的 `/plan` 只是注入一段 prompt。 |
| Git shipping | `@pi-unipi/workflow` 2.20.5 | 只做到 worktree 建立與本機 `git merge`，完全沒有 `gh` PR 流程，不夠用。 |
| aaaav hook | pi 0.87.1 的 `tool_result` 事件 | handler 可以修改模型看到的 `content`（`dist/core/extensions/types.d.ts:836-837,1015`）。`@hsingjui/pi-hooks` 只讀 `.pi/settings.json`，不讀 Claude 的設定。 |
| 派工紀錄與接回 | `pi-herdr-agents` 2.0.4 | 主 process 重啟後不會恢復 watcher（`herdr.ts:246-247`）。但 worktree manifest 會寫入 `paneId`、`sessionFile`、狀態（`launch.ts`），足以讓一個小型 extension 在啟動時重新接回。 |

## 決策

| Question | Answer | Basis | Status |
|---|---|---|---|
| 遷移深度 | 完整遷移，每個決策點都要問使用者 | 使用者 2026-09-25 | confirmed |
| 權限姿態 | worker 一律 yolo | 使用者「yolo 可以」 | confirmed |
| 主 harness | pi 加社群套件 | 上方實測；使用者選擇 | confirmed |
| Claude 模型接法 | `pi-claude-bridge`（Agent SDK，計入訂閱額度） | 條款與 bridge 實測；使用者選擇 | confirmed |
| straw-boss 的去留 | 退役；派工核心改用 `pi-herdr-agents` | 套件實測；使用者選擇 | confirmed |
| 需在 user root 重寫保留的功能 | 派工紀錄與接回（roll-call、pane 重啟後接回）、多主代理協調與交接、shipping-task Git 流程；coworker 二次審查不保留 | 使用者選擇 | confirmed |
| aaaav 的打包位置 | 留在 aaaav repo，加 `package.json#pi` manifest，用 `pi install` 安裝 | 使用者選擇 | confirmed |
| model profile 的表達方式 | tier → model:thinking 與 fallback 寫入套件設定，切換策略即套用另一組設定；prose 只保留理由；拿掉 agent kind 維度 | 使用者選擇 | confirmed |
| plan mode | 不裝 plan mode 套件；`/plan` 保留給 `pi-herdr-agents`，事前規劃由 aaaav-do 的流程負責 | 使用者選擇 | confirmed |
| 非啟用策略的 Gemini／agy tier | 在 pi 的兩組模型中對應到 Codex Luna | 使用者 2026-09-25 回覆「改對應 Codex Luna（建議）」 | confirmed |
| 原策略的 Opus 1M tier（初次對映） | 曾對應 bridge Opus 5.5 200K | 使用者 2026-09-25 初次回覆；後續被上游新證據取代 | superseded |
| 原策略的 Opus 1M tier（更新對映） | 使用 bridge Opus 5.5 1M；將 `pi-claude-bridge` 固定在上游 commit `227f5eb4450a070dfbc083a7fe75b8b35366b941`，待 npm 發布包含 #120 的版本再切回 npm | 使用者 2026-09-25 新方向；上游 commit 與 #127 的測量紀錄 | confirmed |
| 過渡期 | 直接切換；不改壞原本的腳本，而是讓 install／uninstall 支援 `--target`（claude、codex、gemini、pi、full），由使用者用 `--target pi` 加上移除舊目標完成切換；Claude Code 的 binary 與登入保留，作為 bridge 的後端 | 使用者選擇與核准時的修訂 | confirmed |

核心規則已就緒：所有影響可觀察行為的決策皆已確認，沒有待決事項。
