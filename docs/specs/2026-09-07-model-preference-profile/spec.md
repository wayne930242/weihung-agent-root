Status: approved
Approved at: 2026-09-07
Approved from: 使用者確認三級 effort 後回覆「寫吧」

2026-09-07 補充授權：使用者要求 profile 版控，命名當前最佳策略為 codex-first，原有策略為 claude-coding-codex-doc。

# 契約

1. 單一 model-preference-profile.md 定義本期模型與優先順序。
2. 所有預設 boss-say 工作使用 Codex gpt-6-astra；簡單 light 對應 low、一般 medium、複雜或不容許錯誤 high。明確的使用者指定優先。
3. 管理 skill 可依新一期使用者偏好更新 profile，確認參數支援與路由一致性。
4. Claude 與 Codex 根提示引用同一份 profile，安裝後皆可讀取；舊版按工作類型選 Sonnet／Fable／Sol／Luna 的路由由 profile 取代。
5. 兩套具名策略獨立保存，入口指定 codex-first 為當前最佳且啟用策略；管理 skill 支援新增、修訂及切換，Git 保存版本。

遵循 AGENTS.md 的正向表述、讀後修改與驗證要求。保留現有 CLAUDE.md 修改中明確選模型的用意。

Reality anchor：提示詞引用檢查及真實安裝／移除腳本在暫存 home 的整合測試。這些證據驗證設定與可讀性；實際模型遵循需另以真實派工觀察。
