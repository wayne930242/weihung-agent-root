---
name: managing-model-preferences
description: 管理本專案的模型偏好策略；使用者新增、切換策略，或調整優勢模型、派工優先順序與 effort 分級時使用。
---

# 管理模型偏好

1. 讀取同目錄的 [model-preference-profile.md](model-preference-profile.md)，再讀目前啟用及本次指定的策略，確認選擇順序與 effort 分級。一般派工依入口讀取啟用策略。
   完成條件：能說明目前生效的規則與本次要求的差異。
2. 以使用者已提供的偏好決定更新內容；遇到會改變模型或 effort 的未決選擇，一次詢問一個。用目前 harness 的模型清單、CLI 說明或官方文件核對模型識別碼及 effort 參數，區分偏好名稱與實際參數。
   完成條件：每個分級都有明確的模型、effort 與可用的參數依據；無法支援的設定已回報。
3. 透過 `leveraging-tasks` 延續已授權的修改。解析本 skill 的實際來源目錄，在來源 checkout 操作：新增策略寫入 `strategies/<名稱>.md` 並登錄目錄；修訂策略更新該檔；切換策略只更新入口的啟用連結、日期與依據。使用者的本期判斷就是偏好依據。
   完成條件：策略各自保存，入口只指定一套目前最佳且啟用的策略；Git diff 能核對本次新增、修訂或切換。使用者要求版控時，驗證後 scoped commit，回報 commit；push 依使用者授權。
4. 檢查 Claude／Codex 入口與派工參數；在來源 checkout 執行 `bash tests/prompts.sh`、`bash tests/install.sh` 及 `bash tests/uninstall.sh`。對簡單、一般、複雜、不容許錯誤與明確覆寫各走讀一次。
   完成條件：回報各情境的選擇結果，並區分本地驗證、安裝與真實派工證據。
