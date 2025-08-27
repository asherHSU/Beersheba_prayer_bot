# Beersheba Prayer Bot (別是巴代禱事項機器人)
這是一個專為教會小組設計的 LINE Bot，旨在取代傳統在群組中以「接龍」方式更新代禱事項的流程。透過自動化和私訊互動，Bot 能有效減少群組中的訊息量，讓代禱事項的管理更加輕鬆、私密且有效率。

此專案以後端 Flask 應用程式的形式建構，部署於 Google Cloud Functions，並使用 Google Cloud Firestore 作為資料庫。

## ✨ 主要功能
本 Bot 的核心設計是將個人操作引導至私訊完成，而群組管理則由管理員在群組中執行，以最大程度保持群組頻道的整潔。

### 🙋‍♂️ 個人指令 (建議私訊 Bot 使用)
- `加入代禱`: 自動將使用者加入代禱名單。Bot 會獲取您的 LINE 顯示名稱並完成帳號綁定。
- `我的代禱`: 查詢您在當前活躍輪次中的代禱事項。
- `代禱 [事項內容]`: 更新您自己的代禱事項。
- `代禱 同上週`: 自動抓取您上一個輪次的代禱事項內容並更新。
- `修改我的名字 [新名字]`: 修改您在名單上的顯示名稱。

👑 管理員指令 (主要在群組中使用)
- `開始代禱 [截止時間]`: 在群組中發起新一輪的代禱，並通知所有成員。
- `結束代禱`: 結束當前的代禱輪次，並發布最終的代禱事項總結。
- `代禱列表`: 查看當前輪次所有成員的代禱事項列表。
- `名單列表`: (私訊專用) 查看所有成員及其 LINE 帳號的綁定狀態。
- `移除成員 [名字]`: 從名單中移除一位成員。
- `修改成員名字 [舊名字] [新名字]`: (私訊專用) 修改名單上某位成員的名字。
- `名單設定 [名字...]`: (備用) 手動覆蓋整個代禱名單。

### 💡 其他
- `幫助` 或 `help`: 根據您的身份（管理員或一般成員）在私訊中顯示對應的指令說明。在群組中則保持沉默以避免洗頻。
- **自動歡迎訊息**: 當新用戶加入 Bot 好友時，會自動發送歡迎訊息，引導使用者加入代禱名單。

### 🛠️ 技術棧
- **後端框架**: Python, Flask

- **部署平台**: Google Cloud Functions (Gen2)

- **資料庫**: Google Cloud Firestore (NoSQL)

- **LINE SDK**: line-bot-sdk (v2 風格)

## 🚀 設定與部署
### 前置需求
1. Python 3.10+ 環境。

2. Google Cloud SDK (gcloud CLI) 已安裝並完成認證。

3. 一個 LINE Developer 帳號 及一個 Messaging API Channel。

4. 一個 Google Cloud Platform (GCP) 專案，並已啟用以下服務：

    - Cloud Functions API

    - Cloud Run API

    - Cloud Build API

    - Cloud Firestore API

**本地設定**
1. **複製專案:**
```bash
git clone [您的專案 Git URL]
cd Beersheba_prayer_bot
```
2. **安裝依賴:**
```bash
pip install -r requirements.txt
```
**設定環境變數:**
在專案根目錄建立一個 `.env` 檔案，並填入以下內容。此檔案僅供本地測試使用，不會上傳至 GCP。
```
LINE_CHANNEL_SECRET="您的 Channel Secret"
LINE_CHANNEL_ACCESS_TOKEN="您的 Channel Access Token"
GCP_PROJECT_ID="您的 GCP 專案 ID"
TARGET_GROUP_ID="您要讓 Bot 服務的目標 LINE 群組 ID"
```
部署至 Google Cloud Functions
使用以下指令進行部署。請務必將 `[YOUR_..._HERE]` 的部分替換為您自己的實際資訊。
```
gcloud functions deploy prayer-bot-webhook \
  --gen2 \
  --runtime python310 \
  --region asia-east1 \
  --source . \
  --entry-point line_bot_handler_function \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars LINE_CHANNEL_SECRET="[YOUR_CHANNEL_SECRET_HERE]" \
  --set-env-vars LINE_CHANNEL_ACCESS_TOKEN="[YOUR_CHANNEL_ACCESS_TOKEN_HERE]" \
  --set-env-vars GCP_PROJECT_ID="[YOUR_GCP_PROJECT_ID_HERE]" \
  --set-env-vars TARGET_GROUP_ID="[YOUR_TARGET_GROUP_ID_HERE]"
```
部署成功後，將輸出的 HTTPS Trigger URL (`https://.../callback`) 填入 LINE Developers Console 的 Webhook URL 欄位。

### 📁 專案結構

- `main.py`: 包含所有 Bot 邏輯的主程式檔案。

- `requirements.txt`: Python 依賴套件列表。

- `.env`: (本地用) 存放環境變數的檔案。
 
- `.gitignore`: 指定 Git 應忽略的檔案。
 
- `.gcloudignore`: 指定 gcloud CLI 部署時應忽略的檔案。
 
- `picture/`: 存放圖文選單設計圖等圖片資源。

