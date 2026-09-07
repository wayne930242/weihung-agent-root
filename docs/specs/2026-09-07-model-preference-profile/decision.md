# 模型偏好集中管理

以單一 Markdown 記錄每期偏好，讓 boss-say 選擇模型；管理 skill 負責更新。

| Question | Answer | Basis | Status |
|---|---|---|---|
| 本期模型 | Codex Astra | 使用者原始要求 | confirmed |
| effort 分級 | 簡單 light、一般 medium、複雜或不容許錯誤 high | 使用者後續回答 | confirmed |
| 執行修改 | 完成 profile、管理 skill 與路由整合 | 使用者「寫吧」 | confirmed |
| 策略版控 | codex-first 為當前最佳，原有策略保存為 claude-coding-codex-doc；使用 Git 追蹤 | 使用者後續要求 | confirmed |
| 安裝位置 | skill 內的 profile 隨既有雙平台 skill 連結安裝 | scripts/install.sh | grounded |

範圍為本專案的派工偏好與引用入口。既有主會話設定與專用角色 TOML 維持其用途；boss-say 使用明確參數選擇本期模型。待決事項為零。
