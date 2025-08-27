import os
import sys
import datetime
import functions_framework
from flask import Flask, request, abort
from dotenv import load_dotenv

# --- 全域狀態變數 ---
linebot_actual_version = "未知"
linebot_module_imported = False
sdk_import_successful = False
sdk_initialized_successfully = False
db_initialized_successfully = False
firestore_client_version = "未知"
FieldPath = None 

# --- 導入 linebot 主模組 ---
try:
    import linebot
    linebot_module_imported = True
    print(f"INFO (繁中): 成功導入 'linebot' 主模組。")
    try:
        linebot_actual_version = linebot.__version__
        print(f"INFO (繁中): Python line-bot-sdk 版本: {linebot_actual_version}")
    except AttributeError:
        print("警告 (繁中): 無法確定 line-bot-sdk 版本。")
except ImportError as e_linebot_main:
    print(f"嚴重錯誤 (繁中): 導入 'linebot' 主模組失敗: {e_linebot_main}")

# --- 假設是 v1/v2 風格的導入 ---
LineBotApi, WebhookHandler, InvalidSignatureError, MessageEvent, FollowEvent, UnfollowEvent, TextMessageContent, TextSendMessage, SourceUser, SourceGroup = [None] * 10

if linebot_module_imported:
    try:
        from linebot import LineBotApi as GlobalLineBotApi, WebhookHandler as GlobalWebhookHandler
        from linebot.exceptions import InvalidSignatureError as GlobalInvalidSignatureError
        from linebot.models import MessageEvent as GlobalMessageEvent, FollowEvent as GlobalFollowEvent, UnfollowEvent as GlobalUnfollowEvent, TextMessage as GlobalTextMessage, TextSendMessage as GlobalTextSendMessage, SourceUser as GlobalSourceUser, SourceGroup as GlobalSourceGroup
        LineBotApi, WebhookHandler, InvalidSignatureError, MessageEvent, FollowEvent, UnfollowEvent, TextMessageContent, TextSendMessage, SourceUser, SourceGroup = GlobalLineBotApi, GlobalWebhookHandler, GlobalInvalidSignatureError, GlobalMessageEvent, GlobalFollowEvent, GlobalUnfollowEvent, GlobalTextMessage, GlobalTextSendMessage, GlobalSourceUser, GlobalSourceGroup
        sdk_import_successful = True
        print(f"INFO (繁中): 已成功從 linebot.* (v1/v2 風格) 導入核心 SDK 類別。")
    except ImportError as e:
        print(f"嚴重錯誤 (繁中): 導入 LINE SDK 核心類別失敗: {e}")
else:
     print(f"錯誤 (繁中): linebot 主模組導入失敗，無法進行後續導入。")

# --- 導入 Firestore Client ---
try:
    from google.cloud import firestore
    from google.cloud.firestore_v1.field_path import FieldPath as ImportedFieldPath 
    FieldPath = ImportedFieldPath 
    print(f"INFO (繁中): 成功導入 Firestore 相關模組。")
    try:
        firestore_client_version = firestore.__version__
        print(f"INFO (繁中): google-cloud-firestore 版本: {firestore_client_version}")
    except AttributeError:
        print("警告 (繁中): 無法確定 google-cloud-firestore 版本。")
except ImportError as e:
    print(f"嚴重錯誤 (繁中): 導入 Firestore 相關模組失敗: {e}")
    firestore = None
    FieldPath = None 

# --- 載入 .env 與讀取環境變數 ---
load_dotenv()
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
TARGET_GROUP_ID = os.environ.get('TARGET_GROUP_ID')

# --- 初始化 Flask App 和服務 ---
flask_app = Flask(__name__)
db = None
line_bot_api = None 
handler = None      

if firestore: 
    try:
        db = firestore.Client(project=GCP_PROJECT_ID) if GCP_PROJECT_ID else firestore.Client()
        db_initialized_successfully = True
        print(f"INFO (繁中): Firestore Client 初始化完成。")
    except Exception as e: print(f"嚴重錯誤 (繁中): Firestore Client 初始化失敗: {e}")
else: print("嚴重錯誤 (繁中): Firestore 主模組未導入，無法初始化 Client。")

if sdk_import_successful:
    if LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN and LineBotApi and WebhookHandler:
        try:
            line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
            handler = WebhookHandler(LINE_CHANNEL_SECRET)      
            sdk_initialized_successfully = True
            print("INFO (繁中): LINE Bot SDK 初始化完成。")
        except Exception as e: print(f"錯誤 (繁中): LINE Bot SDK 初始化過程中發生錯誤: {e}")
    else: print("錯誤 (繁中): LINE Bot SDK 未能初始化 (缺少金鑰或核心類別)。")
else: print("錯誤 (繁中): 因核心組件導入失敗，無法初始化 LINE Bot SDK。")

# === Flask App 的路由定義 ===
@flask_app.route('/')
def hello_world_flask():
    print("--- ROUTE: / (hello_world_flask) executed ---")
    return (f"LINE Bot 代禱事項小幫手 (診斷模式)<br>"
            f"SDK 初始化: {'成功' if sdk_initialized_successfully else '失敗'}<br>"
            f"DB 初始化: {'成功' if db_initialized_successfully else '失敗'}<br>"
            f"目標群組 ID: {'已設定' if TARGET_GROUP_ID else '未設定'}")

@flask_app.route('/callback', methods=['POST'])
def line_callback_flask():
    print("--- ROUTE: /callback (line_callback_flask) executed ---")
    if not sdk_initialized_successfully or not handler or not line_bot_api:
        abort(500) 
    if not db_initialized_successfully or not db :
        abort(500)
    
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400) 
    except Exception as e:
        print(f"錯誤 (繁中): 處理 Webhook 時發生未預期錯誤: {e}"); abort(500) 
    return 'OK'

# --- 幫助訊息內容 (區分版本) ---

USER_HELP_MESSAGE = """📖 代禱事項小幫手 - 指令說明 📖

🙋 您可以使用的指令 (建議私訊我喔！)
  ▪️ 加入代禱
     (將您自動加入代禱名單)
     
  ▪️ 修改我的名字 [您的新名字]
     (更新您在名單上的顯示名稱)
     
  ▪️ 代禱 [您的事項內容]
     (更新您的代禱事項) 中括號可以不用打，但記得在代禱與事項內容中間需要空格
     
  ▪️ 代禱 同上週
     (使用上週的代禱事項)
     
  ▪️ 我的代禱
     (查詢您目前的代禱事項)
     
  ▪️ 代禱列表
     (查詢所有人的代禱事項)
     
💡 其他
  ▪️ 幫助 或 help
     (顯示此幫助訊息)

💡 範例
    1️⃣ 加入代禱 (第一次使用)
    2️⃣ 代禱 期末考順利
"""

ADMIN_HELP_MESSAGE = """👑 代禱事項小幫手 - 指令說明 (管理員版) 

👥 群組管理指令 (限在群組中操作)
  ▪️ 開始代禱 [截止時間]
  ▪️ 結束代禱
  ▪️ 代禱列表

🙋 個人指令 (可在私訊或群組中使用)
  ▪️ 加入代禱
  ▪️ 修改我的名字 [您的新名字] (私訊專用)
  ▪️ 代禱 [事項]
  ▪️ 代禱 同上週
  ▪️ 我的代禱
  ▪️ 名單列表 (私訊專用)
  ▪️ 修改成員名字 [舊名字] [新名字]
  
💡 其他
  ▪️ 幫助 或 help
     (顯示此幫助訊息)
"""

# --- 輔助函式 ---
def is_group_admin(group_id_check, user_id_check):
    if not db_initialized_successfully or not group_id_check or not user_id_check: return False
    try:
        group_doc_ref = db.collection('prayer_groups').document(group_id_check)
        group_data_snapshot = group_doc_ref.get()
        if group_data_snapshot.exists:
            admin_ids = group_data_snapshot.to_dict().get('admin_user_ids', [])
            return user_id_check in admin_ids
    except Exception as e: print(f"錯誤 (繁中): 檢查管理員權限時發生錯誤: {e}")
    return False

def reply_message_handler(reply_token, reply_text):
    """統一的回覆訊息函式"""
    if reply_text:
        try:
            line_bot_api.reply_message(reply_token, TextSendMessage(text=reply_text))
            print(f"INFO (繁中): 已成功回覆訊息。")
        except Exception as e: print(f"錯誤 (繁中): 回覆訊息時發生錯誤: {e}")
    else:
        print(f"INFO (繁中): 無需回覆訊息。")

# --- 指令處理函式 (Command Handlers) ---

# --- 處理私訊中的 加入代禱 指令 ---
# 這個函式會將使用者加入代禱名單，並在 Firestore 中建立或更新對應的群組文件。
# 如果使用者已經在名單中，則會更新其顯示名稱
def handle_command_join_prayer(user_id):
    """處理私訊中的 加入代禱 指令"""
    if not TARGET_GROUP_ID:
        print("嚴重錯誤 (繁中): 未設定 TARGET_GROUP_ID")
        return "抱歉，Bot 目前設定有誤，暫時無法加入。"
    try:
        profile = line_bot_api.get_profile(user_id)
        user_display_name = profile.display_name
        group_doc_ref = db.collection('prayer_groups').document(TARGET_GROUP_ID)
        
        update_path = f'members.{user_id}' 
        update_data = {'name': user_display_name, 'user_id': user_id}
        
        group_doc = group_doc_ref.get()
        if not group_doc.exists:
            update_data['is_admin'] = True
            group_doc_ref.set({'members': {user_id: update_data}, 'admin_user_ids': [user_id]})
            return f"✅ {user_display_name}，您已成功加入代禱名單，並成為第一位管理員！"
        else:
            members_map = group_doc.to_dict().get('members', {})
            if user_id in members_map:
                if members_map[user_id].get('name') != user_display_name:
                    members_map[user_id]['name'] = user_display_name
                    group_doc_ref.update({'members': members_map})
                    return f"{user_display_name}，您已經在名單中了喔！(已為您更新顯示名稱)"
                return f"{user_display_name}，您已經在代禱名單中了喔！"
            else:
                group_doc_ref.update({update_path: update_data})
                return f"✅ {user_display_name}，您已成功加入代禱名單！"
    except Exception as e: 
        print(f"錯誤 (繁中): 處理 加入代禱 時發生內部錯誤: {e}")
        return "抱歉，加入代禱名單時發生了點問題，請稍後再試。"

# --- 處理私訊或群組中的 代禱 指令 ---
# 這個函式會根據 user_id 自動更新使用者的代禱事項。
# 如果使用者輸入「同上週」，則會抓取上一輪的代禱事項。
# 如果沒有正在進行的輪次，則會回覆錯誤訊息。
def handle_command_update_prayer(user_id, text_received):
    """
    處理私訊或群組中的 代禱 指令。
    根據 user_id 自動更新使用者的代禱事項。
    """
    if not TARGET_GROUP_ID:
        print("嚴重錯誤 (繁中): 未設定 TARGET_GROUP_ID，無法執行 代禱。")
        return "抱歉，Bot 目前設定有誤，暫時無法更新。"

    if not db_initialized_successfully or not db:
        print("嚴重錯誤 (繁中): Firestore 未初始化，無法執行 代禱。")
        return "抱歉，資料庫連線暫時有問題，請稍後再試。"

    try:
        group_doc_ref = db.collection('prayer_groups').document(TARGET_GROUP_ID)
        group_data_snapshot = group_doc_ref.get()

        if not group_data_snapshot.exists:
            return "錯誤：找不到目標群組的設定資料，請聯絡管理員。"
        
        group_data = group_data_snapshot.to_dict()
        members_map = group_data.get('members', {})
        
        # 根據 user_id 檢查用戶是否在名單中
        sender_member_data = members_map.get(user_id)
        
        if not sender_member_data:
            return "抱歉，您尚未加入代禱名單。\n請先輸入 加入代禱"
        
        current_round_id = group_data.get('current_round_id')

        if not current_round_id:
            return "錯誤：目前沒有正在進行中的代禱輪次。"
        
        round_doc_ref = db.collection('prayer_rounds').document(current_round_id)
        round_data_snapshot = round_doc_ref.get()

        if not round_data_snapshot.exists or not round_data_snapshot.to_dict().get('is_active'):
            return "錯誤：目前沒有正在進行中的代禱輪次。"
        
        sender_name = sender_member_data.get('name', 'N/A')
        
        # 解析指令內容
        parts = text_received.split(" ", 1)
        content = ""
        if len(parts) > 1 and parts[1].strip():
            content = parts[1].strip()
        else: # 如果只有 代禱
            return "指令格式錯誤。\n用法：代禱 [您的事項內容]\n或：代禱 同上週"
        
        update_data = {}
        timestamp = firestore.SERVER_TIMESTAMP
        # *** 使用 user_id 作為 entries 的 key ***
        update_path_prefix = f'entries.{user_id}'
        
        if content.lower() == "同上週":
            # --- 「同上週」內容抓取邏輯 ---
            found_previous_text = False
            previous_prayer_text = ""
            current_round_created_time = round_data_snapshot.to_dict().get('created_time')

            if current_round_created_time:
                try:
                    # 查詢該群組所有輪次，按創建時間降序排列，取最近的一個過去輪次
                    rounds_query = db.collection('prayer_rounds') \
                                    .where('group_id', '==', TARGET_GROUP_ID) \
                                    .where('created_time', '<', current_round_created_time) \
                                    .order_by('created_time', direction=firestore.Query.DESCENDING) \
                                    .limit(1) 
                    
                    previous_rounds = list(rounds_query.stream())
                    if previous_rounds:
                        prev_round_data = previous_rounds[0].to_dict()
                        prev_entries = prev_round_data.get('entries', {})
                        # *** 使用 user_id 查找上週事項 ***
                        if user_id in prev_entries and prev_entries[user_id].get('text'):
                            previous_prayer_text = prev_entries[user_id]['text']
                            found_previous_text = True
                except Exception as e_prev_text: 
                    print(f"錯誤 (繁中): 抓取「同上週」內容的 Firestore 查詢時發生錯誤: {e_prev_text}")
            
            if found_previous_text:
                update_data[f'{update_path_prefix}.text'] = previous_prayer_text
                update_data[f'{update_path_prefix}.status'] = 'updated_from_last_week' 
                reply_text = f"✅ 您的代禱事項已更新為上週內容：\n「{previous_prayer_text}」"
            else:
                update_data[f'{update_path_prefix}.text'] = "" 
                update_data[f'{update_path_prefix}.status'] = 'same_as_last_week' 
                reply_text = f"✅ 您的代禱事項已標記為：同上週 (未找到您在上一輪的具體代禱文字)。"
            
            update_data[f'{update_path_prefix}.last_updated'] = timestamp

        elif content: # 新的代禱事項
            update_data[f'{update_path_prefix}.text'] = content
            update_data[f'{update_path_prefix}.status'] = 'updated'
            update_data[f'{update_path_prefix}.last_updated'] = timestamp
            reply_text = f"✅ 您的代禱事項已更新！"
        
        else: # 如果 content 為空字串 (例如用戶只輸入 代禱)
             reply_text = "請在 代禱 後提供您的事項內容，或輸入 同上週。"
        
        if update_data:
            round_doc_ref.update(update_data)
            print(f"INFO (繁中): 使用者 {user_id} ({sender_name}) 更新了事項。")
            
        return reply_text

    except Exception as e:
        print(f"錯誤 (繁中): 處理 代禱 時發生內部錯誤: {e}")
        return "更新您的代禱事項時發生了未預期的錯誤，請稍後再試。"

# --- 處理私訊中的 我的代禱 指令 ---
# 這個函式會查詢使用者在當前活躍輪次中的代禱事項。
def handle_command_my_prayer(user_id):
    """
    處理私訊中的 我的代禱 指令。
    查詢並回覆使用者在當前活躍輪次中的代禱事項。
    """
    if not TARGET_GROUP_ID:
        print("嚴重錯誤 (繁中): 未設定 TARGET_GROUP_ID，無法執行 我的代禱。")
        return "抱歉，Bot 目前設定有誤，暫時無法查詢。 (TGID missing)" # 這種情況需要回覆

    if not db_initialized_successfully or not db:
        print("嚴重錯誤 (繁中): Firestore 未初始化，無法執行 我的代禱。")
        return "抱歉，資料庫連線暫時有問題，請稍後再試。" # 這種情況需要回覆

    try:
        group_doc_ref = db.collection('prayer_groups').document(TARGET_GROUP_ID)
        group_data_snapshot = group_doc_ref.get()

        if not group_data_snapshot.exists:
            return "抱歉，您尚未加入任何代禱名單。\n請先在群組中由管理員發起代禱，或在私訊中輸入 加入代禱。"
        
        group_data = group_data_snapshot.to_dict()
        members_map = group_data.get('members', {})
        
        # 根據 user_id 檢查用戶是否在名單中
        sender_member_data = members_map.get(user_id)
        
        if not sender_member_data:
            return "抱歉，您尚未加入代禱名單。\n請先輸入 加入代禱"
        
        sender_name = sender_member_data.get('name', 'N/A')
        current_round_id = group_data.get('current_round_id')

        if not current_round_id:
            return f"哈囉 {sender_name}！\n目前群組沒有正在進行中的代禱輪次喔。"
        
        round_doc_ref = db.collection('prayer_rounds').document(current_round_id)
        round_data_snapshot = round_doc_ref.get()

        if not round_data_snapshot.exists or not round_data_snapshot.to_dict().get('is_active'):
            return f"哈囉 {sender_name}！\n目前群組沒有正在進行中的代禱輪次喔。"
        
        entries = round_data_snapshot.to_dict().get('entries', {})
        # 使用 user_id 作為 key 來查找代禱事項
        my_entry = entries.get(user_id, {}) 
        
        my_text = my_entry.get('text', '')
        my_status = my_entry.get('status', 'pending')
        display_text = ""

        if my_status == 'same_as_last_week':
            display_text = "同上週 (但未抓取到內容)"
        elif my_status == 'updated_from_last_week':
            display_text = f"{my_text} (同上週內容)" if my_text else "同上週 (內容已抓取但為空)"
        elif my_status == 'pending' and not my_text:
            display_text = "(您尚未更新)"
        elif not my_text:
            display_text = "(內容為空)"
        else:
            display_text = my_text
        
        reply_text = f"哈囉 {sender_name}！\n您在本輪的代禱事項為：\n\n「{display_text}」\n\n您隨時可以在這裡直接用 代禱 [新事項] 來更新喔。"
        return reply_text

    except Exception as e:
        print(f"錯誤 (繁中): 處理 我的代禱 時發生內部錯誤: {e}")
        return "查詢您的代禱事項時發生了未預期的錯誤，請稍後再試。" # 對於未預期錯誤，也給予用戶回饋
    
# --- 處理 開始代禱 指令 ---
# 這個函式會在群組中由管理員發起新的代禱輪次。
def handle_command_start_prayer(group_id, user_id, text_received):
    """
    處理群組中的 開始代禱 指令。
    """
    if not is_group_admin(group_id, user_id):
        return "抱歉，只有本群組代禱事項的管理員才能開始新的代禱輪次。😅"

    try:
        group_doc_ref = db.collection('prayer_groups').document(group_id)
        group_data_snapshot = group_doc_ref.get()
        
        if not group_data_snapshot.exists:
            return "錯誤：找不到群組設定資料。請先透過 加入代禱 建立名單。"
        
        group_data = group_data_snapshot.to_dict()
        members_map = group_data.get('members', {})

        if not isinstance(members_map, dict) or not members_map:
            return "錯誤：此群組尚未有任何成員加入代禱名單。請成員先私訊 Bot 加入代禱。"

        # 檢查是否有正在進行中的輪次
        current_round_id_from_db = group_data.get('current_round_id')
        if current_round_id_from_db:
            round_check_doc = db.collection('prayer_rounds').document(current_round_id_from_db).get()
            if round_check_doc.exists and round_check_doc.to_dict().get('is_active') is True:
                return "資訊：目前已有一個正在進行中的代禱輪次。如要開始新的輪次，請先使用 結束代禱。"
        
        # 從 members map 的 value 中獲取名字列表
        member_names_list = [member_info.get('name') for member_info in members_map.values() if member_info.get('name')]
        
        if not member_names_list:
            return "錯誤：代禱名單為空或成員資料不完整。"

        # 解析截止時間
        parts = text_received.split(" ", 1)
        deadline_text = "無特別截止時間"
        if len(parts) > 1 and parts[1].strip():
            deadline_text = parts[1].strip()

        # 建立新的代禱輪次 ID (使用更唯一的 ID)
        round_timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
        new_round_id = f"{group_id}_{round_timestamp_str}"
        round_doc_ref = db.collection('prayer_rounds').document(new_round_id)

        # 初始化輪次資料 (entries 的 key 現在是 user_id)
        initial_entries = {}
        for uid, member_info in members_map.items():
            initial_entries[uid] = {
                'name': member_info.get('name', '未知名字'), # 將名字也存一份在 entry 中，方便列表顯示
                'text': '', 
                'status': 'pending', 
                'last_updated': firestore.SERVER_TIMESTAMP
            }
        
        round_data = {
            'group_id': group_id, 
            'round_date': datetime.date.today().strftime("%Y-%m-%d"),
            'deadline_text': deadline_text, 
            'is_active': True,
            'entries': initial_entries, 
            'created_by': user_id,
            'created_time': firestore.SERVER_TIMESTAMP
        }
        round_doc_ref.set(round_data) 
        group_doc_ref.update({'current_round_id': new_round_id, 'last_round_started_by': user_id})
        
        # 準備回覆訊息
        reply_text = f"🔔 新一輪代禱已開始！🔔\n截止時間：{deadline_text}\n\n請各位使用以下格式更新您的代禱事項 (可私訊 Bot)：\n代禱 您的事項內容\n或\n代禱 同上週\n\n目前名單與狀態：\n"
        for name in sorted(member_names_list): # 讓名單按字母/筆劃排序
            reply_text += f"▪️ {name}: (待更新)\n"
        reply_text = reply_text.strip()
        
        print(f"INFO (繁中): 群組 {group_id} 已由管理員 {user_id} 開始新輪次 (ID: {new_round_id})。")
        return reply_text

    except Exception as e:
        print(f"錯誤 (繁中): 處理 開始代禱 時發生內部錯誤: {e}")
        return None # 內部錯誤不回覆
    
# --- 處理群組中的 結束代禱 指令 ---
# 這個函式會結束當前活躍的代禱輪次。
def handle_command_end_prayer(group_id, user_id):
    """
    處理群組中的 結束代禱 指令，並在結束時發布最終代禱事項列表。
    """
    if not is_group_admin(group_id, user_id):
        return "抱歉，只有本群組代禱事項的管理員才能結束代禱輪次。😅"

    try:
        group_doc_ref = db.collection('prayer_groups').document(group_id)
        group_data_snapshot = group_doc_ref.get()

        if not group_data_snapshot.exists:
            return "錯誤：找不到此群組的設定資料。"
        
        group_data = group_data_snapshot.to_dict()
        current_round_id = group_data.get('current_round_id')

        if not current_round_id:
            return "資訊：目前沒有正在進行中的代禱輪次可以結束。"
        
        round_doc_ref = db.collection('prayer_rounds').document(current_round_id)
        round_data_snapshot = round_doc_ref.get()

        if not round_data_snapshot.exists:
            # 資料不一致的情況：group 指向一個不存在的 round
            print(f"警告 (繁中): 群組 {group_id} 指向一個不存在的輪次 ID: {current_round_id}。將清除該 ID。")
            group_doc_ref.update({'current_round_id': firestore.DELETE_FIELD})
            return "資訊：目前沒有進行中的代禱輪次可以結束 (已清理無效的輪次記錄)。"
        
        round_data = round_data_snapshot.to_dict()
        if round_data.get('is_active') is False:
            return f"資訊：此代禱輪次已經是結束狀態。"
        
        # --- 新增：獲取並格式化最終的代禱事項列表 ---
        final_list_text = "\n\n📖 本輪最終代禱事項 📖"
        entries = round_data.get('entries', {})
        members_map = group_data.get('members', {})
        
        # 按照成員名字排序
        sorted_members = sorted(members_map.values(), key=lambda x: x.get('name', ''))
        
        if not sorted_members:
            final_list_text += "\n本輪沒有成員或代禱事項。"
        else:
            for member_info in sorted_members:
                uid = member_info.get('user_id')
                name = member_info.get('name')
                
                # 只顯示在 entries 中有記錄的成員
                if uid in entries:
                    entry_data = entries.get(uid, {})
                    item_text = entry_data.get('text', '')
                    status = entry_data.get('status', 'pending')

                    display_text = ""
                    if status == 'same_as_last_week':
                        display_text = "同上週 (但未抓取到內容)" 
                    elif status == 'updated_from_last_week':
                        display_text = f"{item_text} (同上週內容)" if item_text else "同上週 (內容已抓取但為空)"
                    elif status == 'pending' and not item_text:
                        display_text = "(待更新)"
                    elif not item_text:
                        display_text = "(內容為空)"
                    else:
                        display_text = item_text
                    
                    final_list_text += f"\n▪️ {name}：{display_text}"

        final_list_text = final_list_text.strip()
        # --- 格式化列表結束 ---

        # 更新輪次文件，將其標記為不活躍
        round_doc_ref.update({
            'is_active': False,
            'ended_by': user_id,
            'ended_time': firestore.SERVER_TIMESTAMP
        })
        
        # 更新群組文件，移除 current_round_id，表示當前沒有活躍輪次
        group_doc_ref.update({'current_round_id': firestore.DELETE_FIELD})
        
        # 組合最終的回覆訊息
        reply_text = f"{final_list_text}\n\n感謝大家的參與！"
        print(f"INFO (繁中): 群組 {group_id} 的代禱輪次 {current_round_id} 已由管理員 {user_id} 結束。")
        return reply_text

    except Exception as e:
        print(f"錯誤 (繁中): 處理 結束代禱 時發生內部錯誤: {e}")
        return None # 內部錯誤不回覆
    

    
def handle_command_prayer_list(group_id, user_id):
    """
    處理 代禱列表 指令。
    - 在群組中：任何人都可以使用。
    - 在私訊中：僅限管理員使用。
    """
    target_group_id_to_query = group_id

    # 判斷是否為私訊情境
    if not group_id:
        if not TARGET_GROUP_ID:
            return "抱歉，Bot 目前設定有誤 (TGID missing)。"
        
        # # 在私訊中，必須是管理員才能查詢
        # if not is_group_admin(TARGET_GROUP_ID, user_id):
        #     return "抱歉，您不是管理員，無法在私訊中使用此指令。😅"
        
        target_group_id_to_query = TARGET_GROUP_ID
        print(f"INFO (繁中): 管理員 {user_id} 正在透過私訊查詢群組 {target_group_id_to_query} 的代禱列表。")

    try:
        group_doc_ref = db.collection('prayer_groups').document(target_group_id_to_query)
        group_data_snapshot = group_doc_ref.get()

        if not group_data_snapshot.exists:
            return "錯誤：找不到此群組的設定資料。請先透過 加入代禱 建立名單。"
        
        group_data = group_data_snapshot.to_dict()
        current_round_id = group_data.get('current_round_id')

        if not current_round_id:
            return "資訊：目前沒有正在進行中的代禱輪次。"
        
        round_doc_ref = db.collection('prayer_rounds').document(current_round_id)
        round_data_snapshot = round_doc_ref.get()

        if not round_data_snapshot.exists or not round_data_snapshot.to_dict().get('is_active'):
            return "資訊：目前沒有正在進行中的代禱輪次。"
        
        round_data = round_data_snapshot.to_dict()
        deadline_text = round_data.get('deadline_text', "未設定")
        entries = round_data.get('entries', {})
        members_map = group_data.get('members', {})
        
        # 按照成員名字排序
        sorted_members = sorted(members_map.values(), key=lambda x: x.get('name', ''))

        if not sorted_members:
            return f"📖 本輪代禱事項 (截止：{deadline_text}) 📖\n\n名單為空或尚無代禱內容。"
        
        # 根據情境加上不同的標題
        title = f"📖 本輪代禱事項 (截止：{deadline_text}) 📖"
        if not group_id: # 如果是私訊
            title = f"📖 管理員私訊 - 本輪代禱事項 (截止：{deadline_text}) 📖"
            
        reply_text = title
        
        for member_info in sorted_members:
            uid = member_info.get('user_id')
            name = member_info.get('name')
            
            # 只顯示在 entries 中有記錄的成員
            if uid in entries:
                entry_data = entries.get(uid, {})
                item_text = entry_data.get('text', '')
                status = entry_data.get('status', 'pending')

                display_text = ""
                if status == 'same_as_last_week':
                    display_text = "同上週 (但未抓取到內容)" 
                elif status == 'updated_from_last_week':
                    display_text = f"{item_text} (同上週內容)" if item_text else "同上週 (內容已抓取但為空)"
                elif status == 'pending' and not item_text:
                    display_text = "(待更新)"
                elif not item_text:
                    display_text = "(內容為空)"
                else:
                    display_text = item_text
                
                reply_text += f"\n▪️ {name}：{display_text}"

        return reply_text.strip()

    except Exception as e:
        print(f"錯誤 (繁中): 處理 代禱列表 時發生內部錯誤: {e}")
        return None # 內部錯誤不回覆


# --- 處理私訊中的 開始代禱 指令 ---
# 這個函式會在私訊中由管理員發起新的代禱輪次。
# 主要邏輯與群組版類似，但會在私訊中回覆。
# 這個函式會檢查使用者是否為管理員，並在 Firestore 中建立新的代禱輪次。
# 如果沒有正在進行的輪次，則會建立新的輪次並推播通知到目標群組。
# 如果已經有活躍輪次，則會回覆錯誤訊息。
# 注意：這個函式只在私訊中使用，與群組版的 handle_command_start_prayer 不同。
def handle_command_start_prayer_dm(user_id, text_received):
    """
    處理管理員在私訊中使用的 開始代禱 指令。
    """
    if not TARGET_GROUP_ID:
        return "抱歉，Bot 目前設定有誤 (TGID missing)。"

    # 步驟 1：權限檢查
    if not is_group_admin(TARGET_GROUP_ID, user_id):
        return "抱歉，您不是此代禱群組的管理員，無法使用此指令。😅"

    try:
        group_doc_ref = db.collection('prayer_groups').document(TARGET_GROUP_ID)
        group_data_snapshot = group_doc_ref.get()

        if not group_data_snapshot.exists:
            return "錯誤：找不到目標群組的設定資料。"
        
        group_data = group_data_snapshot.to_dict()
        members_map = group_data.get('members', {})

        if not members_map:
            return "錯誤：此群組尚未有任何成員加入代禱名單。"

        # 步驟 2：檢查是否已有活躍輪次
        current_round_id_from_db = group_data.get('current_round_id')
        if current_round_id_from_db:
            round_check_doc = db.collection('prayer_rounds').document(current_round_id_from_db).get()
            if round_check_doc.exists and round_check_doc.to_dict().get('is_active'):
                return "資訊：目前已有一個正在進行中的代禱輪次。如要開始新的輪次，請先使用 結束代禱。"

        # 步驟 3：建立新輪次 (與群組版邏輯相同)
        member_names_list = [member_info.get('name') for member_info in members_map.values() if member_info.get('name')]
        
        parts = text_received.split(" ", 1)
        deadline_text = "無特別截止時間"
        if len(parts) > 1 and parts[1].strip():
            deadline_text = parts[1].strip()

        round_timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
        new_round_id = f"{TARGET_GROUP_ID}_{round_timestamp_str}"
        round_doc_ref = db.collection('prayer_rounds').document(new_round_id)

        initial_entries = {}
        for uid, member_info in members_map.items():
            initial_entries[uid] = {
                'name': member_info.get('name', '未知名字'),
                'text': '', 'status': 'pending', 
                'last_updated': firestore.SERVER_TIMESTAMP
            }
        
        round_data = {
            'group_id': TARGET_GROUP_ID, 
            'round_date': datetime.date.today().strftime("%Y-%m-%d"),
            'deadline_text': deadline_text, 'is_active': True,
            'entries': initial_entries, 'created_by': user_id,
            'created_time': firestore.SERVER_TIMESTAMP
        }
        round_doc_ref.set(round_data) 
        group_doc_ref.update({'current_round_id': new_round_id, 'last_round_started_by': user_id})

        # 步驟 4：準備群組通知訊息並主動推播 (Push Message)
        group_notification_text = f"🔔 新一輪代禱已開始！🔔\n截止時間：{deadline_text}\n\n請各位私訊我來更新您的代禱事項喔！"
        try:
            line_bot_api.push_message(TARGET_GROUP_ID, TextSendMessage(text=group_notification_text))
            print(f"INFO (繁中): 已成功推播「開始代禱」通知到群組 {TARGET_GROUP_ID}。")
        except Exception as e_push:
            print(f"錯誤 (繁中): 推播「開始代禱」通知到群組時發生錯誤: {e_push}")
            return f"輪次已在後台建立，但推播通知到群組時失敗，請檢查日誌。\n錯誤: {e_push}"

        # 步驟 5：回覆私訊給管理員
        return f"✅ 已成功在目標群組發起新一輪代禱，並已發送通知！"

    except Exception as e:
        print(f"錯誤 (繁中): 處理私訊 開始代禱 時發生內部錯誤: {e}")
        return "處理指令時發生未預期的錯誤，請稍後再試。"
    
# --- 處理私訊中的 結束代禱 指令 ---
# 這個函式會結束當前活躍的代禱輪次，並發布最終代禱事項列表。
def handle_command_end_prayer_dm(user_id):
    """
    處理管理員在私訊中使用的 結束代禱 指令。
    """
    if not TARGET_GROUP_ID:
        return "抱歉，Bot 目前設定有誤 (TGID missing)。"

    # 步驟 1：權限檢查
    if not is_group_admin(TARGET_GROUP_ID, user_id):
        return "抱歉，您不是此代禱群組的管理員，無法使用此指令。😅"

    try:
        group_doc_ref = db.collection('prayer_groups').document(TARGET_GROUP_ID)
        group_data_snapshot = group_doc_ref.get()

        if not group_data_snapshot.exists:
            return "錯誤：找不到目標群組的設定資料。"
        
        group_data = group_data_snapshot.to_dict()
        current_round_id = group_data.get('current_round_id')

        if not current_round_id:
            return "資訊：目前沒有正在進行中的代禱輪次可以結束。"
        
        round_doc_ref = db.collection('prayer_rounds').document(current_round_id)
        round_data_snapshot = round_doc_ref.get()

        if not round_data_snapshot.exists or not round_data_snapshot.to_dict().get('is_active'):
            return "資訊：此代禱輪次已經是結束狀態。"
        
        # 步驟 2：獲取最終代禱列表 (與群組版邏輯相同)
        round_data = round_data_snapshot.to_dict()
        final_list_text = "\n\n📖 本輪最終代禱事項 📖"
        entries = round_data.get('entries', {})
        members_map = group_data.get('members', {})
        sorted_members = sorted(members_map.values(), key=lambda x: x.get('name', ''))
        
        if not sorted_members:
            final_list_text += "\n本輪沒有成員或代禱事項。"
        else:
            for member_info in sorted_members:
                uid = member_info.get('user_id')
                name = member_info.get('name')
                if uid in entries:
                    entry_data = entries.get(uid, {})
                    item_text = entry_data.get('text', '(待更新)')
                    final_list_text += f"\n▪️ {name}：{item_text}"
        
        # 步驟 3：更新 Firestore
        round_doc_ref.update({'is_active': False, 'ended_by': user_id, 'ended_time': firestore.SERVER_TIMESTAMP})
        group_doc_ref.update({'current_round_id': firestore.DELETE_FIELD})
        
        # 步驟 4：準備群組通知訊息並主動推播
        group_notification_text = f"✅ 代禱輪次已結束！\n{final_list_text.strip()}\n\n感謝大家的參與！"
        try:
            line_bot_api.push_message(TARGET_GROUP_ID, TextSendMessage(text=group_notification_text))
            print(f"INFO (繁中): 已成功推播「結束代禱」通知到群組 {TARGET_GROUP_ID}。")
        except Exception as e_push:
            print(f"錯誤 (繁中): 推播「結束代禱」通知到群組時發生錯誤: {e_push}")
            return f"輪次已在後台結束，但推播通知到群組時失敗，請檢查日誌。\n錯誤: {e_push}"

        # 步驟 5：回覆私訊給管理員
        return f"✅ 已成功在目標群組結束代禱輪次，並已發送最終總結！"

    except Exception as e:
        print(f"錯誤 (繁中): 處理私訊 結束代禱 時發生內部錯誤: {e}")
        return "處理指令時發生未預期的錯誤，請稍後再試。"

# --- 處理私訊中的 幫助 指令 ---
# 這個函式會根據使用者是否為管理員，回覆不同的幫助訊息。
# 在群組中則不回覆任何訊息，以避免洗頻。
def handle_command_help(user_id, group_id):
    """
    處理 幫助 指令。
    - 在私訊中：根據使用者是否為管理員，回傳不同的訊息。
    - 在群組中：不回覆任何訊息，以避免洗頻。
    """
    # 如果指令來自群組，則不回覆
    if group_id:
        print(f"INFO (繁中): 在群組 {group_id} 中收到 幫助 指令，將不予回覆以避免洗頻。")
        return None

    # 如果指令來自私訊，則檢查其管理員身份
    # 注意：is_group_admin 需要使用全域的 TARGET_GROUP_ID 來判斷
    if is_group_admin(TARGET_GROUP_ID, user_id):
        print(f"INFO (繁中): 管理員 {user_id} 在私訊中請求了幫助指令。")
        return ADMIN_HELP_MESSAGE
    else:
        print(f"INFO (繁中): 一般成員 {user_id} 在私訊中請求了幫助指令。")
        return USER_HELP_MESSAGE


def handle_command_list_members(user_id, group_id=None):
    """
    處理   指令 (私訊專用)。
    僅限管理員在私訊中使用，以查看成員列表與綁定狀態。
    """
    # 此指令現在設計為私訊專用，避免在群組中洗頻
    if group_id:
        print(f"INFO (繁中): 在群組 {group_id} 中收到 名單列表 指令，將不予回覆以避免洗頻。")
        return None

    if not TARGET_GROUP_ID:
        return "抱歉，Bot 目前設定有誤 (TGID missing)。"

    # # 權限檢查：必須是管理員
    if not is_group_admin(TARGET_GROUP_ID, user_id):
        return "抱歉，您不是此代禱群組的管理員，無法使用此指令。😅"

    try:
        group_doc_ref = db.collection('prayer_groups').document(TARGET_GROUP_ID)
        group_data_snapshot = group_doc_ref.get()

        if not group_data_snapshot.exists:
            return "錯誤：找不到目標群組的設定資料。"
        
        group_data = group_data_snapshot.to_dict()
        members_map = group_data.get('members', {})

        if not members_map:
            return "目前代禱名單中沒有任何成員。"

        reply_text = "👥 管理員私訊 - 目前代禱名單成員 👥\n"
        
        # 按照成員名字排序
        sorted_members = sorted(members_map.values(), key=lambda x: x.get('name', ''))
        
        for member_info in sorted_members:
            name = member_info.get('name', '未知名字')
            member_user_id = member_info.get('user_id')
            reply_text += f"\n▪️ {name} (ID: {member_user_id})"
        
        return reply_text.strip()

    except Exception as e:
        print(f"錯誤 (繁中): 處理 名單列表 時發生內部錯誤: {e}")
        return None # 內部錯誤不回覆
    
# --- 處理私訊中的 修改成員名字 指令 ---
# 這個函式會在私訊中由管理員修改成員的名字。
# 主要邏輯是檢查使用者是否為管理員，
# 並在 Firestore 中更新對應的成員名字。
def handle_command_edit_member_name(user_id, text_received, group_id=None):
    """
    處理 修改成員名字 [舊名字] [新名字] 指令 (私訊專用)。
    """
    # 此指令現在設計為私訊專用，避免在群組中洗頻
    if group_id:
        print(f"INFO (繁中): 在群組 {group_id} 中收到 修改成員名字 指令，將不予回覆以避免洗頻。")
        return None

    if not TARGET_GROUP_ID:
        return "抱歉，Bot 目前設定有誤 (TGID missing)。"

    # 權限檢查：必須是管理員
    if not is_group_admin(TARGET_GROUP_ID, user_id):
        return "抱歉，您不是此代禱群組的管理員，無法使用此指令。😅"

    try:
        parts = text_received.split(" ")
        # 指令格式應為: 修改成員名字 舊名字 新名字，共3個部分
        if len(parts) != 3 or not parts[1].strip() or not parts[2].strip():
            return "指令格式錯誤。\n用法：修改成員名字 [舊名字] [新名字]"

        old_name = parts[1].strip()
        new_name = parts[2].strip()

        group_doc_ref = db.collection('prayer_groups').document(TARGET_GROUP_ID)
        group_data_snapshot = group_doc_ref.get()

        if not group_data_snapshot.exists or 'members' not in group_data_snapshot.to_dict():
            return "錯誤：群組名單未設定，無法修改名字。"

        members_map = group_data_snapshot.to_dict().get('members', {})
        
        # 檢查新名字是否已存在於名單中
        for member_data in members_map.values():
            if member_data.get('name', '').lower() == new_name.lower():
                return f"錯誤：新名字「{new_name}」已存在於名單中，無法修改。"

        # 根據舊名字找到對應的 user_id
        target_user_id = None
        for uid, member_data in members_map.items():
            if member_data.get('name', '').lower() == old_name.lower():
                target_user_id = uid
                break
        
        if not target_user_id:
            return f"錯誤：名單中找不到成員「{old_name}」。"

        # 步驟 1: 更新 prayer_groups 文件中的成員名字
        update_path_for_name = f'members.{target_user_id}.name'
        group_doc_ref.update({
            update_path_for_name: new_name,
            'last_updated_by': user_id, 
            'last_updated_time': firestore.SERVER_TIMESTAMP
        })
        
        update_round_entry_text = ""
        current_round_id = group_data_snapshot.to_dict().get('current_round_id')
        if current_round_id:
            try:
                round_doc_ref = db.collection('prayer_rounds').document(current_round_id)
                round_data_snapshot = round_doc_ref.get()
                # 步驟 2: 如果有活躍輪次，也同步更新輪次中的名字
                if round_data_snapshot.exists and target_user_id in round_data_snapshot.to_dict().get('entries', {}):
                    update_path_for_round_name = f'entries.{target_user_id}.name'
                    round_doc_ref.update({
                        update_path_for_round_name: new_name
                    })
                    update_round_entry_text = "同時已更新當前代禱輪次中的名字。"
            except Exception as e_round_update:
                print(f"警告 (繁中): 更新輪次 {current_round_id} 的成員名字時發生錯誤: {e_round_update}")
                update_round_entry_text = "但更新當前代禱輪次時遇到問題，請檢查日誌。"

        return f"✅ 已成功將成員「{old_name}」的名字修改為「{new_name}」。 {update_round_entry_text}".strip()

    except Exception as e:
        print(f"錯誤 (繁中): 處理 修改成員名字 時發生內部錯誤: {e}")
        return None # 內部錯誤不回覆

# --- 處理私訊中的 修改我的名字 指令 ---
# 這個函式會在私訊中由使用者修改自己的名字。
def handle_command_edit_my_name(user_id, text_received):
    """
    處理使用者在私訊中使用的 修改我的名字 [新名字] 指令。
    """
    if not TARGET_GROUP_ID:
        return "抱歉，Bot 目前設定有誤 (TGID missing)。"

    try:
        parts = text_received.split(" ", 1)
        if len(parts) < 2 or not parts[1].strip():
            return "指令格式錯誤。\n用法：修改我的名字 [您的新名字]"

        new_name = parts[1].strip()

        group_doc_ref = db.collection('prayer_groups').document(TARGET_GROUP_ID)
        group_data_snapshot = group_doc_ref.get()

        if not group_data_snapshot.exists or user_id not in group_data_snapshot.to_dict().get('members', {}):
            return "抱歉，您尚未加入代禱名單，無法修改名字。\n請先輸入 加入代禱"

        members_map = group_data_snapshot.to_dict().get('members', {})
        old_name = members_map[user_id].get('name', '未知')

        # 檢查新名字是否已存在於名單中 (排除自己)
        for uid, member_data in members_map.items():
            if uid != user_id and member_data.get('name', '').lower() == new_name.lower():
                return f"錯誤：新名字「{new_name}」已存在於名單中，無法修改。"

        # 步驟 1: 更新 prayer_groups 文件中的成員名字
        update_path_for_name = f'members.{user_id}.name'
        group_doc_ref.update({
            update_path_for_name: new_name,
            'last_updated_by': user_id, 
            'last_updated_time': firestore.SERVER_TIMESTAMP
        })
        
        update_round_entry_text = ""
        current_round_id = group_data_snapshot.to_dict().get('current_round_id')
        if current_round_id:
            try:
                round_doc_ref = db.collection('prayer_rounds').document(current_round_id)
                round_data_snapshot = round_doc_ref.get()
                # 步驟 2: 如果有活躍輪次，也同步更新輪次中的名字
                if round_data_snapshot.exists and user_id in round_data_snapshot.to_dict().get('entries', {}):
                    update_path_for_round_name = f'entries.{user_id}.name'
                    round_doc_ref.update({
                        update_path_for_round_name: new_name
                    })
                    update_round_entry_text = "同時已更新您在當前代禱輪次中的名字。"
            except Exception as e_round_update:
                print(f"警告 (繁中): 更新輪次 {current_round_id} 的成員名字時發生錯誤: {e_round_update}")
                update_round_entry_text = "但更新當前代禱輪次時遇到問題，請檢查日誌。"

        return f"✅ 成功！您的名字已從「{old_name}」修改為「{new_name}」。 {update_round_entry_text}".strip()

    except Exception as e:
        print(f"錯誤 (繁中): 處理 修改我的名字 時發生內部錯誤: {e}")
        return None # 內部錯誤不回覆





# ... (其他指令的處理函式，例如 handle_command_start_prayer 等，可以陸續加入)

# === LINE Bot SDK 事件處理器 ===
if sdk_initialized_successfully and handler:
    
    @handler.add(FollowEvent)
    def handle_follow(event):
        try:
            profile = line_bot_api.get_profile(event.source.user_id)
            reply_text = f"哈囉 {profile.display_name}！👋\n我是代禱事項小幫手。\n\n如果您想加入代禱名單，請直接在這裡輸入指令：\n加入代禱"
            reply_message_handler(event.reply_token, reply_text)
            print(f"INFO (繁中): 已發送歡迎訊息給新好友 {profile.display_name} ({event.source.user_id})。")
        except Exception as e: print(f"錯誤 (繁中): 回覆新好友歡迎訊息時發生錯誤: {e}")
    
    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_text_message(event):
        user_id = event.source.user_id
        text_received = event.message.text.strip()
        reply_text = None
        
        # --- 指令路由器 (Router) ---
        if isinstance(event.source, SourceUser):
            print(f"INFO (繁中): 收到來自用戶 {user_id} 的私訊: {text_received}")
            if text_received.lower() in ["幫助", "help"]:
                reply_text = handle_command_help(user_id, None) 
            elif text_received.lower() == "加入代禱":
                reply_text = handle_command_join_prayer(user_id)
            elif text_received.lower() == "代禱列表":
                reply_text = handle_command_prayer_list(None, user_id)
            elif text_received.lower().startswith("代禱"):
                reply_text = handle_command_update_prayer(user_id, text_received)
            elif text_received.lower() == "我的代禱":
                reply_text = handle_command_my_prayer(user_id)
            elif text_received.lower().startswith("開始代禱"):
                reply_text = handle_command_start_prayer_dm(user_id, text_received)
            elif text_received.lower() == "結束代禱":
                reply_text = handle_command_end_prayer_dm(user_id)
            elif text_received.lower() == "名單列表":
                reply_text = handle_command_list_members(user_id, None)
            elif text_received.lower().startswith("修改成員名字"):
                reply_text = handle_command_edit_member_name(user_id, text_received, None)
            elif text_received.lower().startswith("修改我的名字"):
                reply_text = handle_command_edit_my_name(user_id, text_received)


        elif isinstance(event.source, SourceGroup):
            group_id = event.source.group_id
            print(f"INFO (繁中): 收到來自群組 {group_id} (使用者 {user_id}) 的訊息: {text_received}")
            if text_received.lower() in ["幫助", "help"]:
                # 呼叫新的幫助函式，傳入 group_id
                reply_text = handle_command_help(user_id, group_id)
            elif text_received.lower().startswith("開始代禱"):
                reply_text = handle_command_start_prayer(group_id, user_id, text_received)
            elif text_received.lower() == "結束代禱":
                reply_text = handle_command_end_prayer(group_id, user_id)
            elif text_received.lower() == "代禱列表":
                # 呼叫函式，傳入實際的 group_id
                reply_text = handle_command_prayer_list(group_id, user_id)
            
            # ... 其他群組指令的呼叫
            
        # --- 統一回覆 ---
        reply_message_handler(event.reply_token, reply_text)

# === Google Cloud Functions 的 HTTP 進入點函式 ===
@functions_framework.http
def line_bot_handler_function(request_ff):
    if not sdk_initialized_successfully or not db_initialized_successfully or not TARGET_GROUP_ID:
        print("嚴重錯誤 (繁中): 服務未完全初始化 (SDK, DB, 或 TARGET_GROUP_ID)。")
        return "服務因內部設定錯誤而不可用。", 503
    with flask_app.request_context(request_ff.environ):
        try:
            return flask_app.full_dispatch_request()
        except Exception as e:
            print(f"錯誤 (繁中): Flask App 分派請求時發生錯誤: {e}")
            return "伺服器內部錯誤。", 500
