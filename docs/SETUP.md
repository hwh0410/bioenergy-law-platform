# 生質能法規平台：內部登入部署說明

這是 GitHub Pages + Vue + Firebase Google 登入 + Cloud Run + 私有 Google Sheets 白名單的登入原型，**尚非完整法規資料庫**。

## A. GitHub Pages 網頁

1. 將本 Pull Request 合併到 main。
2. 在 GitHub Repository 的 Settings → Pages → Build and deployment，選擇 GitHub Actions。
3. 在 Settings → Secrets and variables → Actions → **Variables**，從 Firebase 專案的 firebaseConfig 複製以下四項（只填值、不加引號）：

| GitHub Repository variable | Firebase 原始欄位 |
| --- | --- |
| VITE_FIREBASE_API_KEY | apiKey |
| VITE_FIREBASE_AUTH_DOMAIN | authDomain |
| VITE_FIREBASE_PROJECT_ID | projectId |
| VITE_FIREBASE_APP_ID | appId |

4. GitHub → Actions → Deploy Vue to GitHub Pages → Run workflow。
5. 打開 https://hwh0410.github.io/bioenergy-law-platform/ 。

未填變數時會顯示設定提示，不會直接開放內部功能。Firebase Web 初始化參數可用於前端，但**不要將服務帳戶 JSON、私人憑證或 API 私密金鑰放進 GitHub**。

## B. Google Sheets 使用者白名單

建立**非公開** Google 試算表，第一個工作表命名為 Users，第一列欄名順序為：

uid | email | name | role | enabled

例如下一列：

firebase_uid | name@example.com | 小組管理員 | admin | TRUE

role 僅允許 admin、editor、viewer。enabled 為 TRUE 才允許存取。UID 在第一次 Google 登入後可從網頁複製。試算表不得開放給「知道連結的人」。

## C. Cloud Run 權限驗證 API（第二個建置里程碑）

1. 在 Firebase 所對應的 Google Cloud 專案啟用 Google Sheets API、Cloud Run、Cloud Build、Artifact Registry；啟用帳單與預算提醒。
2. 建立專用服務帳戶（例如 bioenergy-auth-api）；將該服務帳戶 Email 在 Google Sheets「共用」中設定為檢視者。
3. 以此服務帳戶部署 backend 目錄至 Cloud Run，設定環境變數 SPREADSHEET_ID、FRONTEND_ORIGINS=https://hwh0410.github.io。
4. 在 GitHub Repository Variables 加入 VITE_API_BASE_URL（Cloud Run HTTPS URL），重新執行網頁部署。
5. 透過 Firebase Token 呼叫 /api/me；未登入為 401、不在名單為 403、名單不可用為 503。

Cloud Run 的 HTTP 入口可以公開供瀏覽器送出 Token，但後端每次仍執行身分及 Sheets 授權檢查。所有未來受保護 API 都必須加入 require_member 或更嚴格的角色檢查，不能只靠前端隱藏按鈕。

## D. 本機測試

在 frontend 目錄：

~~~powershell
Copy-Item .env.example .env.local
notepad .env.local
npm install
npm run dev
~~~

將 .env.local 填入 Firebase Web 設定。本機 VITE_BASE_PATH=/。Firebase Authentication 授權網域也要有 localhost。

## 安全提醒

GitHub Pages 上的檔案全部可以被訪客下載。內部法規解讀、業主資料、文件及權限白名單不得放到公開 JSON 中。Google 登入成功並不等於團隊授權成功。
