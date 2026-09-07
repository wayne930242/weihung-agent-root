# 驗證

| Requirement | Evidence | Result |
|---|---|---|
| 單一當期 profile | 來源檢查：model-preference-profile.md 指定唯一啟用策略 codex-first；模型、分級及優先順序集中在該策略檔 | pass |
| Astra 三級派工參數 | 文件走讀：簡單 → low、一般 → medium、複雜 → high、不容許錯誤 → high；使用者明確指定優先。模型為 gpt-6-astra，harness 公開模型清單支援 low／medium／high | pass |
| 管理 skill | SKILL.md 走讀涵蓋讀取現況、確認差異、核對參數、修改來源及驗證；可由偏好更新要求觸發 | pass |
| 雙平台入口與安裝 | bash tests/prompts.sh、bash tests/install.sh、bash tests/uninstall.sh 全部 exit 0；暫存 home 的 Claude／Codex skill 連結指向同一來源，cmp 確認 profile 內容相同，移除後連結不存在 | pass |
| 具名策略版控 | codex-first 與 claude-coding-codex-doc 獨立存檔；後者對照改版前 git HEAD:CLAUDE.md 及原工作區修正保存。安裝測試新增兩個平台、兩套策略的 cmp，三套測試重新執行全部 exit 0 | pass |

git diff --check 通過。使用者既有 CLAUDE.md 修改的明確模型選擇要求已保留於 profile 路由。

實際模型是否依提示選級尚未以真實派工驗證。使用者授權將此變更納入本地 Git commit；尚未安裝到使用者 home 或 push。提交結果以 Git log 為準。
