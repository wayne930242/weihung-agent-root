---
name: "Model Profile"
description: "查看或切換模型偏好策略，也可新增與修訂策略"
argument-hint: "[策略名稱｜status｜要新增或修訂的偏好]"
---

管理本機的模型偏好 profile：`~/.claude/skills/managing-model-preferences/`。

本次要求：$ARGUMENTS

依下列判斷處理，全程使用 `managing-model-preferences` skill：

- 沒有給參數，或參數是 `status`、`list`：讀取 `model-preference-profile.md`，回報目前啟用的策略、啟用日期、選擇依據，以及策略目錄中的其他選項。只讀不改。
- 參數是策略目錄中的名稱：切換啟用策略，只更新 profile 入口的啟用連結、日期與選擇依據，策略檔本身不動。
- 參數描述的是新的或調整後的偏好：依 skill 的步驟新增 `strategies/<名稱>.md` 並登錄目錄，或修訂既有策略檔。

切換與修訂都在來源 checkout（`~/.claude/skills/managing-model-preferences` 的 symlink 目標）操作，改完回報 Git diff 摘要。
