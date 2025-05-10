import os
import sys
from flask import Flask, request, abort
from dotenv import load_dotenv 

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent




# --- 從環境變數讀取 LINE Bot 的設定 ---
# 在部署到 Cloud Functions 時，我們會將這些值設定為環境變數
# 為了方便在本機測試 (如果需要)，您可以暫時直接填寫，但部署前務必改回從環境變數讀取
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '37ba890565925240e244b9ba976e1b58')
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'dLJ1lyK0BrOA7TnRMlODdSdADUti65H1m62hWTvwG8DSqSdyb6jYdKHxQFrwX9WZv6SHMhBdIuoeZJd2leXnqceXa/arasNIg2+Yw7JQzM5ftMEemETZMibapjfb0zMsONfdAEQZF2kS+5MU/PvkAwdB04t89/1O/w1cDnyilFU=')

# --- 初始化 Flask App ---
app = Flask(__name__)

# --- 初始化 LINE Bot SDK ---
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# --- 主 Flask 路由，這會是我們在 LINE Developer Console 設定的 Webhook URL ---
@app.route("/callback", methods=['POST'])
def callback():
    # 取得 X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # 取得 request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body) # 方便在 Cloud Functions Log 查看收到的內容

    # 處理 webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature. Please check your channel secret/access token.")
        abort(400)
    except Exception as e:
        app.logger.error(f"Error occurred: {e}")
        abort(500)

    return 'OK'

# --- 處理 LINE 文字訊息事件 ---
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        user_id = event.source.user_id # 取得使用者 ID
        text_received = event.message.text # 取得使用者傳來的文字

        app.logger.info(f"Received message from user {user_id}: {text_received}")

        # 基本的回應，確認 Bot 活著
        reply_text = f"我收到你的訊息了： '{text_received}'"

        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

# --- Cloud Functions 的進入點 ---
# Google Cloud Functions 會尋找名為 'main' 或與您在部署時指定的進入點名稱相同的 Flask app。
# 如果您的 Flask app 物件名稱是 'app' (如本例)，並且您的檔名是 'main.py'，
# 您在部署時指定的進入點 (entry point) 通常會是 'app'。
# (或者，您可以定義一個名為主函數的函式，直接呼叫 app.run()，但對於 Cloud Functions HTTP 觸發，直接暴露 app 物件更常見)

# 為了讓 Cloud Functions (Python 3.7+) 能找到 Flask app:
# 如果檔名是 main.py，Cloud Functions 會預期有一個名為 'app' 的 Flask 物件。
# 或者，您可以定義一個名為主函數的函式，例如：
# def prayer_bot_webhook(request):
#     return app(request.environ, request.start_response)
# 然後在部署時指定 prayer_bot_webhook 為進入點。
# 目前，我們保持 'app' 作為 Flask 物件，部署時指定 'app' 為進入點即可。

if __name__ == "__main__":
    # 這段是為了方便在本機執行測試 (需要手動設定環境變數或直接填寫金鑰)
    # 部署到 Cloud Functions 時，這段不會被執行
    # 您需要額外工具如 ngrok 來將本機服務暴露給 LINE Platform 才能在本機完整測試 Webhook
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)