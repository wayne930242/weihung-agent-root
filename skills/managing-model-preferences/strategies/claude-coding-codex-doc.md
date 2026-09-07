# claude-coding-codex-doc

保存日期：2026-09-07。
來源：本次改版前的 CLAUDE.md 模型分工，包含工作區既有的 UI/UX 明確模型選擇修正。

## 選擇順序

使用者本次明確指定優先。其餘依原有順序：

1. 最複雜的委派工作沿用主代理當前模型。
2. 文件撰寫委派給 `codex`。
3. 程式撰寫、調查與查詢使用 Claude `sonnet`。
4. 其餘工作沿用主代理當前模型。

直接指示的簡單工作由主代理完成。需要獨立工作環境的任務走 Straw Boss，其餘自足片段可使用 subagent。

## 原有專用選擇

| 情境 | 選擇 |
|---|---|
| 撰寫或大幅改寫文章 | Codex `gpt-5.6-sol`；effort 沿用設定 |
| 翻譯、格式整理、資料擷取等機械工作 | Codex `gpt-5.6-luna`，effort `low` |
| 新 UI/UX 設計的審查與修訂 | 明確指定 Codex 模型，至少 `gpt-5.6-sol`；effort 沿用設定 |
| 其他 Codex 文件工作 | 沿用 Codex 設定的模型與 effort |

原有策略在 Opus 主代理遇到極端複雜工作時，建議移交至 `claude-fable-5-1`。實際權限移交流程依 Straw Boss 的 `handoff-orchestrator` 與 `docs/roles.md` 辦理。

## 套用

本策略保存原有模型分工。重新啟用前，以目前環境確認上述模型及繼承設定可用，解析出實際模型與 effort 後明確帶入派工參數。遇到不可用的模型，回報限制並由使用者決定替代選擇。
