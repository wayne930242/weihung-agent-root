# 設計

沿用 skills 目錄安裝先例，將 profile 放在 managing-model-preferences 內，兩個根提示透過各自的已安裝 skill 路徑讀取。這個可替換的設定介面使每期只需更新一份檔案；相較新增 shared 安裝規則，既有 skill 安裝與移除即可涵蓋完整生命週期。

管理 skill 提供新增、修訂、切換、參數核對與驗證步驟。profile 為固定入口，指向 strategies/ 內的一套啟用策略；策略內容各自保存，以 Git 追蹤修訂。派工呼叫端讀取入口及啟用策略，傳入 kind、model、effort。CLI adapter 將使用者的 light 轉成 Codex low。原生專用角色與主會話設定屬不同介面，boss-say 以明確派工參數套用偏好。

使用 tests/prompts.sh 檢查引用與淘汰路由，tests/install.sh 與 tests/uninstall.sh 檢查雙平台 skill 連結及 profile 的可讀性與移除。
