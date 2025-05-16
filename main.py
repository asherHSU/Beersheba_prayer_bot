import os
import sys
import datetime # 用於處理日期時間
import functions_framework
from flask import Flask, request, abort
from dotenv import load_dotenv

# --- 全域狀態變數 ---
linebot_actual_version = "未知"
linebot_module_imported = False
sdk_import_successful = False
sdk_initialized_successfully = False
db_initialized_successfully = False

# --- 導入 linebot 主模組並嘗試打印版本 ---
try:
    import linebot
    linebot_module_imported = True
    print(f"INFO (繁中): 成功導入 'linebot' 主模組。")
    try:
        linebot_actual_version = linebot.__version__
        print(f"INFO (繁中): Python line-bot-sdk 版本 (透過 __version__): {linebot_actual_version}")
    except AttributeError:
        print("警告 (繁中): 無法透過 __version__ 確定 line-bot-sdk 版本。")
except ImportError as e_linebot_main:
    print(f"嚴重錯誤 (繁中): 導入 'linebot' 主模組失敗: {e_linebot_main}")

# --- 假設是 v1/v2 風格的導入 ---
LineBotApi = None
WebhookHandler = None
InvalidSignatureError = None
MessageEvent = None
TextMessageContent = None 
TextSendMessage = None   
SourceUser = None
SourceGroup = None

if linebot_module_imported:
    try:
        from linebot import LineBotApi as GlobalLineBotApi
        from linebot import WebhookHandler as GlobalWebhookHandler
        from linebot.exceptions import InvalidSignatureError as GlobalInvalidSignatureError
        from linebot.models import (
            MessageEvent as GlobalMessageEvent,
            TextMessage as GlobalTextMessage, 
            TextSendMessage as GlobalTextSendMessage, 
            SourceUser as GlobalSourceUser,
            SourceGroup as GlobalSourceGroup
        )
        LineBotApi = GlobalLineBotApi
        WebhookHandler = GlobalWebhookHandler
        InvalidSignatureError = GlobalInvalidSignatureError
        MessageEvent = GlobalMessageEvent
        TextMessageContent = GlobalTextMessage 
        TextSendMessage = GlobalTextSendMessage
        SourceUser = GlobalSourceUser
        SourceGroup = GlobalSourceGroup
        
        sdk_import_successful = True
        print(f"INFO (繁中): 已成功從 linebot.* (v1/v2 風格) 導入核心 SDK 類別。")
    except ImportError as e_import_v1v2:
        print(f"嚴重錯誤 (繁中): 嘗試以 v1/v2 風格從 linebot.* 導入核心類別失敗: {e_import_v1v2}")
    except Exception as e_generic_import:
        print(f"嚴重錯誤 (繁中): 以 v1/v2 風格導入 LINE SDK 核心類別時發生未知錯誤: {e_generic_import}")
else:
     print(f"錯誤 (繁中): linebot 主模組導入失敗，無法進行後續 SDK 類別導入。")


# --- 導入 Firestore Client ---
from google.cloud import firestore

# --- 載入 .env 檔案中的環境變數 ---
load_dotenv()

# --- 從環境變數讀取設定 ---
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')

# --- 全域的 Flask app 實例 ---
flask_app = Flask(__name__)

# --- 初始化 Firestore Client ---
db = None
try:
    if GCP_PROJECT_ID:
        db = firestore.Client(project=GCP_PROJECT_ID)
        print(f"INFO (繁中): Firestore Client 初始化完成 (指定專案 ID: {GCP_PROJECT_ID})。")
    else:
        db = firestore.Client()
        print(f"INFO (繁中): Firestore Client 初始化完成 (未指定專案 ID)。")
    db_initialized_successfully = True
except Exception as e_firestore_init:
    print(f"嚴重錯誤 (繁中): Firestore Client 初始化失敗: {e_firestore_init}")

# --- 初始化 LINE Bot SDK (使用 v1/v2 風格) ---
line_bot_api = None 
handler = None      

if sdk_import_successful:
    if LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN and LineBotApi and WebhookHandler:
        try:
            line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
            handler = WebhookHandler(LINE_CHANNEL_SECRET)      
            sdk_initialized_successfully = True
            print("INFO (繁中): LINE Bot SDK (v1/v2 風格) 初始化完成。")
        except Exception as e_sdk_init:
            print(f"錯誤 (繁中): LINE Bot SDK (v1/v2 風格) 初始化過程中發生錯誤: {e_sdk_init}")
    else:
        if not (LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN): print("警告 (繁中): Channel Secret 或 Access Token 未設定。")
        if not (LineBotApi and WebhookHandler): print("警告 (繁中): LineBotApi 或 WebhookHandler 類別導入不完整。")
        print("錯誤 (繁中): LINE Bot SDK (v1/v2 風格) 未能初始化 (缺少金鑰或核心類別)。")
else:
    print("錯誤 (繁中): 因核心組件導入失敗，無法初始化 LINE Bot SDK。")

# --- 管理員權限檢查輔助函式 ---
def is_group_admin(group_id_check, user_id_check):
    if not db_initialized_successfully or not db or not group_id_check or not user_id_check:
        return False
    try:
        group_doc_ref = db.collection('prayer_groups').document(group_id_check)
        group_data_snapshot = group_doc_ref.get()
        if group_data_snapshot.exists:
            return group_data_snapshot.to_dict().get('admin_user_id') == user_id_check
    except Exception as e:
        print(f"錯誤 (繁中): 檢查管理員權限時發生錯誤 for group {group_id_check}, user {user_id_check}: {e}")
    return False

# === Flask App 的路由定義 ===
@flask_app.route('/')
def hello_world_flask():
    status_message = f"LINE Bot - 代禱事項小幫手 (v1/v2 風格導入)<br>"
    status_message += f"偵測到 SDK 版本: {linebot_actual_version}<br>"
    status_message += f"SDK 核心組件導入狀態: {'成功' if sdk_import_successful else '失敗'}<br>"
    status_message += f"SDK 初始化狀態: {'成功' if sdk_initialized_successfully else '失敗'}<br>"
    status_message += f"Firestore Client 初始化狀態: {'成功' if db_initialized_successfully else '失敗'}<br>"
    return status_message

@flask_app.route('/callback', methods=['POST'])
def line_callback_flask():
    print("INFO (繁中): Flask app 的 /callback 路由被 LINE 呼叫。")
    if not sdk_initialized_successfully or not handler or not line_bot_api:
        print("錯誤 (繁中): LINE SDK 未完全初始化，無法處理 Webhook。")
        abort(500) 
    if not db_initialized_successfully or not db :
        print("錯誤 (繁中): Firestore Client 未初始化，無法處理資料庫相關請求。")
        abort(500)

    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print(f"INFO (繁中): Request body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("錯誤 (繁中): 簽名驗證失敗。")
        abort(400) 
    except Exception as e:
        print(f"錯誤 (繁中): 處理 Webhook 時發生未預期錯誤: {e}")
        abort(500) 
    return 'OK'

# --- 幫助訊息內容 ---
HELP_MESSAGE = """📖 代禱事項小幫手 - 指令說明 📖

👥 **群組設定與管理 (限管理員)**
  ▪️ `/名單設定 [名字1] [名字2] ...`
     範例: `/名單設定 詩雅 良宏`
     (設定名單，執行者成為管理員)

  ▪️ `/開始代禱 [截止時間文字]`
     範例: `/開始代禱 週五晚上`
     (發起新一輪代禱)

  ▪️ `/結束代禱`
     (結束當前代禱輪次)

  ▪️ `/移除成員 [名字]`
     範例: `/移除成員 詩雅`
     (從代禱名單及當前輪次中移除成員)

🙋 **個人操作 (所有成員可用)**
  ▪️ `/代禱列表`
     (查看本輪代禱事項)

  ▪️ `/綁定我的名字 [您在名單上的名字]`
     範例: `/綁定我的名字 詩雅`
     (綁定您的LINE帳號到名單名字)

  ▪️ `/代禱 [您的事項內容]`
     範例: `/代禱 為家人健康禱告`
     (更新您的代禱事項)

  ▪️ `/代禱 同上週`
     (將您的代禱事項標記為與上週相同，並嘗試抓取上週內容)

💡 **其他**
  ▪️ `/幫助` 或 `/help`
     (顯示此幫助訊息)

✨ 同心守望，彼此代禱！ ✨
"""

# --- LINE Bot SDK 事件處理器 ---
if sdk_initialized_successfully and handler:
    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_text_message(event):
        user_id = event.source.user_id if hasattr(event.source, 'user_id') else '未知用戶ID'
        text_received = event.message.text.strip()
        reply_token = event.reply_token
        
        group_id = None
        source_type_str = "未知來源"
        should_reply_with_message = False 
        reply_text = None 

        if isinstance(event.source, SourceUser):
            source_type_str = f"用戶 ({user_id})"
            print(f"INFO (繁中): 收到來自 {source_type_str} 的私訊: {text_received}")
            if text_received.lower() == "/幫助" or text_received.lower() == "/help":
                reply_text = HELP_MESSAGE
                should_reply_with_message = True
        elif isinstance(event.source, SourceGroup):
            group_id = event.source.group_id
            source_type_str = f"群組 ({group_id})"
            print(f"INFO (繁中): 收到來自 {source_type_str} (使用者 {user_id}) 的訊息: {text_received}")

            if text_received.lower() == "/幫助" or text_received.lower() == "/help":
                reply_text = HELP_MESSAGE
                should_reply_with_message = True
            
            elif text_received.lower().startswith("/名單設定"):
                # ... (與上一版相同的 /名單設定 邏輯) ...
                # (確保在成功或用戶格式錯誤時設定 reply_text 和 should_reply_with_message = True)
                # (內部錯誤只 print)
                if not group_id: reply_text = "「名單設定」指令限群組內使用。"; should_reply_with_message = True
                elif not db_initialized_successfully or not db: print("ERROR (繁中): Firestore db 未初始化，無法執行 /名單設定");
                else:
                    try:
                        parts = text_received.split(" ", 1)
                        if len(parts) > 1 and parts[1].strip():
                            member_names_str = parts[1].strip()
                            raw_member_list = [name.strip() for name in member_names_str.split(" ") if name.strip()]
                            if raw_member_list:
                                group_doc_ref = db.collection('prayer_groups').document(group_id)
                                new_members_map = {name: {'name': name, 'user_id': None} for name in raw_member_list}
                                admin_display_name = "您"
                                try: 
                                    if line_bot_api and user_id != '未知用戶ID':
                                        profile = line_bot_api.get_profile(user_id)
                                        admin_display_name = f"「{profile.display_name}」"
                                except Exception as e_profile: print(f"警告 (繁中): 獲取 user_id {user_id} 的 profile 失敗: {e_profile}")
                                data_to_set = {'members': new_members_map, 'admin_user_id': user_id, 'last_updated_by': user_id, 'last_updated_time': firestore.SERVER_TIMESTAMP}
                                group_doc_ref.set(data_to_set, merge=True) 
                                display_names = list(new_members_map.keys())
                                reply_text = f"✅ 代禱名單已更新！目前名單：\n- " + "\n- ".join(display_names) + f"\n\nℹ️ {admin_display_name} 已被設為本群組代禱事項的管理員。"
                                should_reply_with_message = True
                                print(f"INFO (繁中): 群組 {group_id} 的名單已由 {user_id} 更新為: {display_names}. {user_id} is now admin.")
                            else: reply_text = "名單設定格式錯誤：請在指令後提供至少一個名字。\n範例：/名單設定 詩雅 良宏"; should_reply_with_message = True
                        else: reply_text = "名單設定指令用法：\n/名單設定 [名字1] [名字2] ..."; should_reply_with_message = True
                    except Exception as e: print(f"錯誤 (繁中): 處理 /名單設定 時發生內部錯誤: {e}")
            
            elif text_received.lower().startswith("/移除成員"): # 新增指令
                if not group_id: reply_text = "「移除成員」指令限群組內使用。"; should_reply_with_message = True
                elif not db_initialized_successfully or not db: print("ERROR (繁中): Firestore db 未初始化");
                elif not is_group_admin(group_id, user_id): reply_text = "抱歉，只有管理員才能移除成員。😅"; should_reply_with_message = True
                else:
                    try:
                        parts = text_received.split(" ", 1)
                        if len(parts) < 2 or not parts[1].strip():
                            reply_text = "指令格式錯誤。\n用法：`/移除成員 [要移除的名字]`"; should_reply_with_message = True
                        else:
                            name_to_remove = parts[1].strip()
                            group_doc_ref = db.collection('prayer_groups').document(group_id)
                            group_data_snapshot = group_doc_ref.get()
                            if not group_data_snapshot.exists or 'members' not in group_data_snapshot.to_dict():
                                reply_text = "錯誤：群組名單未設定或格式不正確。"; should_reply_with_message = True
                            else:
                                members_map = group_data_snapshot.to_dict().get('members', {})
                                actual_name_key_to_remove = None
                                for name_key, member_data in members_map.items():
                                    if member_data.get('name','').lower() == name_to_remove.lower():
                                        actual_name_key_to_remove = name_key # 使用 Firestore map 中的原始 key
                                        break
                                
                                if not actual_name_key_to_remove:
                                    reply_text = f"錯誤：名單中找不到成員「{name_to_remove}」。"; should_reply_with_message = True
                                else:
                                    # 從 members map 中移除
                                    members_map.pop(actual_name_key_to_remove, None)
                                    group_doc_ref.update({'members': members_map, 'last_updated_by': user_id, 'last_updated_time': firestore.SERVER_TIMESTAMP})
                                    
                                    # 同時從當前活躍輪次的 entries 中移除 (如果存在)
                                    current_round_id = group_data_snapshot.to_dict().get('current_round_id')
                                    if current_round_id:
                                        round_doc_ref = db.collection('prayer_rounds').document(current_round_id)
                                        # 使用 FieldPath 刪除 map 中的特定鍵
                                        round_doc_ref.update({f'entries.{firestore.FieldPath([actual_name_key_to_remove]).path}': firestore.DELETE_FIELD})
                                        print(f"INFO (繁中): 已從輪次 {current_round_id} 的 entries 中移除 {actual_name_key_to_remove}。")

                                    reply_text = f"✅ 已從代禱名單及當前輪次中移除成員：「{actual_name_key_to_remove}」。"; should_reply_with_message = True
                                    print(f"INFO (繁中): 群組 {group_id} 的成員 {actual_name_key_to_remove} 已由管理員 {user_id} 移除。")
                    except Exception as e:
                        print(f"錯誤 (繁中): 處理 /移除成員 時發生內部錯誤: {e}")


            elif text_received.lower().startswith("/開始代禱"):
                # ... (與上一版相同的 /開始代禱 邏輯，確保成功或用戶錯誤時設定 should_reply_with_message = True) ...
                if not group_id: reply_text = "「開始代禱」指令限群組內使用。"; should_reply_with_message = True
                elif not db_initialized_successfully or not db: print("ERROR (繁中): Firestore db 未初始化"); 
                elif not is_group_admin(group_id, user_id): reply_text = "抱歉，只有管理員才能開始新的代禱輪次。😅"; should_reply_with_message = True
                else:
                    try:
                        group_doc_ref = db.collection('prayer_groups').document(group_id); group_data_snapshot = group_doc_ref.get()
                        if not group_data_snapshot.exists: reply_text = "錯誤：找不到群組設定。請先用「/名單設定」。"; should_reply_with_message = True
                        else:
                            group_data = group_data_snapshot.to_dict()
                            if 'members' not in group_data or not isinstance(group_data['members'], dict) or not group_data['members']: reply_text = "錯誤：尚未設定名單。請先用「/名單設定」。"; should_reply_with_message = True
                            else:
                                member_list = list(group_data['members'].keys()) 
                                if not member_list: reply_text = "錯誤：代禱名單為空。"; should_reply_with_message = True
                                else:
                                    parts = text_received.split(" ", 1); deadline_text = "無特別截止時間"
                                    if len(parts) > 1 and parts[1].strip(): deadline_text = parts[1].strip()
                                    round_date_str = datetime.date.today().strftime("%Y-%m-%d"); current_round_id = f"{group_id}_{round_date_str}"
                                    round_doc_ref = db.collection('prayer_rounds').document(current_round_id)
                                    # 在開始新輪次時，為每個人初始化 'previous_text' (如果需要精確的上週內容)
                                    initial_entries = {}
                                    for name in member_list:
                                        initial_entries[name] = {
                                            'text': '', 'status': 'pending', 
                                            'last_updated': firestore.SERVER_TIMESTAMP
                                            # 'previous_text': '' # 之後可以考慮從更早的輪次讀取
                                        }
                                    round_data = {'group_id': group_id, 'round_date': round_date_str, 'deadline_text': deadline_text, 'is_active': True, 'entries': initial_entries, 'created_by': user_id, 'created_time': firestore.SERVER_TIMESTAMP}
                                    round_doc_ref.set(round_data) # 會覆蓋當天已有的輪次
                                    group_doc_ref.update({'current_round_id': current_round_id, 'last_round_started_by': user_id})
                                    reply_text = f"🔔 新一輪代禱已開始！🔔\n截止時間：{deadline_text}\n\n請各位使用以下格式更新：\n`/代禱 您的事項內容`\n或\n`/代禱 同上週`\n\n名單與狀態：\n";_=[reply_text := reply_text + f"▪️ {name}: (待更新)\n" for name in member_list];reply_text = reply_text.strip()
                                    should_reply_with_message = True
                                    print(f"INFO (繁中): 群組 {group_id} 已由管理員 {user_id} 開始新輪次 (ID: {current_round_id})。")
                    except Exception as e: print(f"錯誤 (繁中): 處理 /開始代禱 時發生內部錯誤: {e}")


            elif text_received.lower() == "/結束代禱":
                # ... (與上一版相同的 /結束代禱 邏輯) ...
                if not group_id: reply_text = "「結束代禱」指令限群組內使用。"; should_reply_with_message = True
                elif not db_initialized_successfully or not db: print("ERROR (繁中): Firestore db 未初始化");
                elif not is_group_admin(group_id, user_id): reply_text = "抱歉，只有管理員才能結束代禱輪次。😅"; should_reply_with_message = True
                else:
                    try:
                        group_doc_ref = db.collection('prayer_groups').document(group_id); group_data_snapshot = group_doc_ref.get()
                        if not group_data_snapshot.exists: reply_text = "錯誤：找不到群組設定資料。"; should_reply_with_message = True
                        else:
                            group_data = group_data_snapshot.to_dict(); current_round_id = group_data.get('current_round_id')
                            if not current_round_id: reply_text = "目前沒有進行中的代禱輪次可以結束。"; should_reply_with_message = True
                            else:
                                round_doc_ref = db.collection('prayer_rounds').document(current_round_id); round_data_snapshot = round_doc_ref.get()
                                if not round_data_snapshot.exists: reply_text = f"錯誤：找不到輪次資料 (ID: {current_round_id})。"; should_reply_with_message = True
                                elif round_data_snapshot.to_dict().get('is_active') is False: reply_text = f"資訊：此代禱輪次 (ID: {current_round_id}) 已經是結束狀態。"; should_reply_with_message = True
                                else:
                                    round_doc_ref.update({'is_active': False, 'ended_by': user_id, 'ended_time': firestore.SERVER_TIMESTAMP})
                                    reply_text = f"✅ 代禱輪次 (ID: {current_round_id}) 已由您結束。\n感謝大家的參與！"; should_reply_with_message = True
                                    print(f"INFO (繁中): 群組 {group_id} 的輪次 {current_round_id} 已由管理員 {user_id} 結束。")
                    except Exception as e: print(f"錯誤 (繁中): 處理 /結束代禱 時發生內部錯誤: {e}")
            
            elif text_received.lower().startswith("/代禱列表"):
                # ... (與上一版相同的 /代禱列表 邏輯) ...
                if not group_id: reply_text = "「代禱列表」指令限群組內使用。"; should_reply_with_message = True
                elif not db_initialized_successfully or not db: print("ERROR (繁中): Firestore db 未初始化");
                else:
                    try:
                        group_doc_ref = db.collection('prayer_groups').document(group_id); group_data_snapshot = group_doc_ref.get()
                        if not group_data_snapshot.exists: reply_text = "錯誤：找不到群組設定。請先用「/名單設定」。"; should_reply_with_message = True
                        else:
                            group_data = group_data_snapshot.to_dict()
                            if 'current_round_id' not in group_data or not group_data['current_round_id']: reply_text = "目前沒有進行中的代禱輪次。"; should_reply_with_message = True
                            else:
                                current_round_id = group_data['current_round_id']; round_doc_ref = db.collection('prayer_rounds').document(current_round_id); round_data_snapshot = round_doc_ref.get()
                                if not round_data_snapshot.exists: reply_text = f"錯誤：找不到輪次資料 (ID: {current_round_id})。"; should_reply_with_message = True
                                else:
                                    round_data = round_data_snapshot.to_dict(); deadline_text = round_data.get('deadline_text', "未設定"); entries = round_data.get('entries', {})
                                    member_map_from_group = group_data.get('members', {}); member_list_sorted = list(member_map_from_group.keys()) if member_map_from_group else []
                                    display_order = []
                                    if member_list_sorted:
                                        for name in member_list_sorted:
                                            if name in entries and name not in display_order: display_order.append(name)
                                        all_names_in_round = list(entries.keys())
                                        for name in all_names_in_round: 
                                            if name not in display_order: display_order.append(name)
                                    else: display_order = list(entries.keys()) if entries else []
                                    if not display_order: reply_text = f"📖 本輪代禱事項 (截止：{deadline_text}) 📖\n\n名單為空或尚無代禱內容。"
                                    else:
                                        reply_text = f"📖 本輪代禱事項 (截止：{deadline_text}) 📖"
                                        for name in display_order:
                                            entry_data = entries.get(name)
                                            if entry_data:
                                                item_text = entry_data.get('text', ''); status = entry_data.get('status', 'pending')
                                                if status == 'same_as_last_week' or status == 'updated_from_last_week': item_text = f"{item_text} (同上週)" if status == 'updated_from_last_week' and item_text else "同上週"
                                                elif status == 'pending' and not item_text: item_text = "(待更新)"
                                                elif not item_text: item_text = "(內容為空)"
                                                reply_text += f"\n▪️ {name}：{item_text}"
                                            else: reply_text += f"\n▪️ {name}：(資料錯誤)"
                                    reply_text = reply_text.strip()
                                    should_reply_with_message = True
                                    print(f"INFO (繁中): 群組 {group_id} 查詢了代禱列表 (ID: {current_round_id})。")
                    except Exception as e: print(f"錯誤 (繁中): 處理 /代禱列表 時發生內部錯誤: {e}")

            elif text_received.lower().startswith("/綁定我的名字"):
                # ... (與上一版相同的 /綁定我的名字 邏輯) ...
                if not group_id: reply_text = "「綁定我的名字」指令限群組內使用。"; should_reply_with_message = True
                elif not db_initialized_successfully or not db: print("ERROR (繁中): Firestore db 未初始化");
                else:
                    try:
                        parts = text_received.split(" ", 1)
                        if len(parts) < 2 or not parts[1].strip(): reply_text = "指令格式錯誤。\n用法：`/綁定我的名字 您在名單上的名字`"; should_reply_with_message = True
                        else:
                            name_to_bind = parts[1].strip(); group_doc_ref = db.collection('prayer_groups').document(group_id); group_data_snapshot = group_doc_ref.get()
                            if not group_data_snapshot.exists or 'members' not in group_data_snapshot.to_dict(): reply_text = "錯誤：群組名單未設定。"; should_reply_with_message = True
                            else:
                                members_map = group_data_snapshot.to_dict().get('members', {}); actual_name_in_list = None
                                for name_key_in_map, member_data_in_map in members_map.items():
                                    if member_data_in_map.get('name', '').lower() == name_to_bind.lower(): actual_name_in_list = member_data_in_map.get('name'); break
                                if not actual_name_in_list: reply_text = f"抱歉，名字「{name_to_bind}」未在名單中。"; should_reply_with_message = True
                                else:
                                    current_bound_user_id = members_map[actual_name_in_list].get('user_id')
                                    if current_bound_user_id and current_bound_user_id != user_id: reply_text = f"抱歉，「{actual_name_in_list}」已被其他用戶綁定。"; should_reply_with_message = True
                                    else:
                                        for name_key_to_unbind, member_data_to_unbind in members_map.items():
                                            if member_data_to_unbind.get('user_id') == user_id and name_key_to_unbind != actual_name_in_list : members_map[name_key_to_unbind]['user_id'] = None
                                        members_map[actual_name_in_list]['user_id'] = user_id
                                        group_doc_ref.update({'members': members_map, 'last_updated_by': user_id, 'last_updated_time': firestore.SERVER_TIMESTAMP})
                                        reply_text = f"✅ 成功！您的帳號已綁定到「{actual_name_in_list}」。\n以後可用 `/代禱 [事項]` 更新。"; should_reply_with_message = True
                                        print(f"INFO (繁中): 群組 {group_id} 中，使用者 {user_id} 綁定了名字 {actual_name_in_list}。")
                    except Exception as e: print(f"錯誤 (繁中): 處理 /綁定我的名字 時發生內部錯誤: {e}")

            elif text_received.lower().startswith("/代禱"):
                if "列表" in text_received.lower(): pass 
                elif not group_id: reply_text = "「代禱」更新指令限群組內使用。"; should_reply_with_message = True
                elif not db_initialized_successfully or not db: print("ERROR (繁中): Firestore db 未初始化");
                else:
                    try:
                        group_doc_ref = db.collection('prayer_groups').document(group_id); group_data_snapshot = group_doc_ref.get()
                        if not group_data_snapshot.exists: reply_text = "錯誤：找不到群組設定資料。"; should_reply_with_message = True
                        else:
                            group_data = group_data_snapshot.to_dict()
                            if 'current_round_id' not in group_data or not group_data['current_round_id'] or \
                               'members' not in group_data or not isinstance(group_data['members'], dict) or not group_data['members']: reply_text = "錯誤：沒有進行中的代禱或名單未設定。"; should_reply_with_message = True
                            else:
                                current_round_id = group_data['current_round_id']; members_map = group_data['members']; round_doc_ref = db.collection('prayer_rounds').document(current_round_id)
                                sender_name_in_list = None
                                for name_key, member_data in members_map.items():
                                    if member_data.get('user_id') == user_id: sender_name_in_list = member_data.get('name'); break
                                if not sender_name_in_list: reply_text = "抱歉，您的帳號尚未綁定名字。\n請用：`/綁定我的名字 [您在名單上的名字]`"; should_reply_with_message = True
                                else:
                                    parts = text_received.split(" ", 1); content = ""
                                    if len(parts) > 1 and parts[1].strip(): content = parts[1].strip()
                                    else: reply_text = "指令格式錯誤。\n用法：`/代禱 [事項]` 或 `/代禱 同上週`"; content = None; should_reply_with_message = True 
                                    if content is not None: 
                                        update_data = {}; timestamp = firestore.SERVER_TIMESTAMP
                                        if content.lower() == "同上週":
                                            # --- 「同上週」內容抓取邏輯 ---
                                            previous_prayer_text = "(找不到上週內容)" # 預設
                                            try:
                                                rounds_query = db.collection('prayer_rounds') \
                                                                .where('group_id', '==', group_id) \
                                                                .where('is_active', 'in', [True, False]) \
                                                                .where('created_time', '<', round_doc_ref.get().to_dict().get('created_time', datetime.datetime.now(datetime.timezone.utc))) \
                                                                .order_by('created_time', direction=firestore.Query.DESCENDING) \
                                                                .limit(1)
                                                previous_rounds = list(rounds_query.stream())
                                                if previous_rounds:
                                                    prev_round_data = previous_rounds[0].to_dict()
                                                    prev_entries = prev_round_data.get('entries', {})
                                                    if sender_name_in_list in prev_entries and prev_entries[sender_name_in_list].get('text'):
                                                        previous_prayer_text = prev_entries[sender_name_in_list]['text']
                                                        update_data[f'entries.{sender_name_in_list}.text'] = previous_prayer_text
                                                        update_data[f'entries.{sender_name_in_list}.status'] = 'updated_from_last_week' # 新狀態
                                                        reply_text = f"✅ {sender_name_in_list} 的代禱事項已更新為上週內容：\n「{previous_prayer_text}」"
                                                    else:
                                                        update_data[f'entries.{sender_name_in_list}.text'] = "" 
                                                        update_data[f'entries.{sender_name_in_list}.status'] = 'same_as_last_week' # 維持原標記
                                                        reply_text = f"✅ {sender_name_in_list} 的代禱事項已更新為：同上週 (但未找到具體內容，請直接更新)。"
                                                else:
                                                    update_data[f'entries.{sender_name_in_list}.text'] = "" 
                                                    update_data[f'entries.{sender_name_in_list}.status'] = 'same_as_last_week' # 維持原標記
                                                    reply_text = f"✅ {sender_name_in_list} 的代禱事項已標記為：同上週 (未找到更早的代禱輪次)。"
                                            except Exception as e_prev_text:
                                                print(f"錯誤 (繁中): 抓取「同上週」內容時發生錯誤: {e_prev_text}")
                                                update_data[f'entries.{sender_name_in_list}.text'] = "" 
                                                update_data[f'entries.{sender_name_in_list}.status'] = 'same_as_last_week' # 出錯時，維持原標記
                                                reply_text = f"✅ {sender_name_in_list} 的代禱事項已標記為：同上週 (抓取內容時出錯)。"
                                            # --- 「同上週」內容抓取邏輯結束 ---
                                            update_data[f'entries.{sender_name_in_list}.last_updated'] = timestamp
                                            should_reply_with_message = True
                                        elif content: 
                                            update_data[f'entries.{sender_name_in_list}.text'] = content; update_data[f'entries.{sender_name_in_list}.status'] = 'updated'; update_data[f'entries.{sender_name_in_list}.last_updated'] = timestamp
                                            reply_text = f"✅ {sender_name_in_list} 的代禱事項已更新！"; should_reply_with_message = True
                                        else: reply_text = "請在 `/代禱` 後提供事項或輸入 `同上週`。"; should_reply_with_message = True
                                        if update_data:
                                            round_doc_ref.update(update_data)
                                            print(f"INFO (繁中): 群組 {group_id} 中，{sender_name_in_list} ({user_id}) 更新了事項。")
                    except Exception as e: print(f"錯誤 (繁中): 處理 /代禱 更新時發生內部錯誤: {e}")
            
            # 如果是群組訊息，但沒有匹配到任何已知指令 (且不是 /幫助)
            if group_id and not should_reply_with_message:
                 print(f"INFO (繁中): 群組 {group_id} 中收到無法識別的指令: '{text_received}'，不進行回覆。")
                 reply_text = None 

        # --- 發送回覆 ---
        if should_reply_with_message and reply_text:
            if sdk_initialized_successfully and line_bot_api:
                try:
                    line_bot_api.reply_message(reply_token, TextSendMessage(text=reply_text))
                    print(f"INFO (繁中): 已成功回覆訊息給 {source_type_str} (使用者 {user_id})")
                except Exception as e: print(f"錯誤 (繁中): 回覆訊息時發生錯誤: {e}")
            else: print("錯誤 (繁中): SDK 未初始化，無法發送回覆。")
        elif not should_reply_with_message : 
             print(f"INFO (繁中): 來源 {source_type_str} 的訊息 '{text_received}' 被判斷為無需回覆。")
else:
    print("警告 (繁中): LINE 事件處理器未附加，因為 handler 未初始化或核心組件導入失敗。")

# --- Google Cloud Functions 的 HTTP 進入點函式 ---
@functions_framework.http
def line_bot_handler_function(request_ff):
    if not sdk_initialized_successfully:
        print("嚴重錯誤 (繁中): LINE Bot SDK 未成功初始化。")
        return "服務因內部SDK設定錯誤而不可用。", 503
    if not db_initialized_successfully:
        print("嚴重錯誤 (繁中): Firestore Client 未初始化。")
        return "服務因內部資料庫設定錯誤而不可用。", 503
        
    with flask_app.request_context(request_ff.environ):
        try:
            return flask_app.full_dispatch_request()
        except Exception as e:
            print(f"錯誤 (繁中): Flask App 分派請求時發生錯誤: {e}")
            return "伺服器內部錯誤。", 500
