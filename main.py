from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent, UnfollowEvent
import os
import psycopg2
#from add_calander import get_settle_info
from add_calander import get_settle_info, transform_style, save_file, read_schedule, main, output_path

app = Flask(__name__)

# Configurations
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME", "")
CODE = "0"

# LINE Bot API Setup
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


# Database Connection Function
def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


# Routes
@app.route("/")
def hello_world():
    return "hello world!"

# # アプリにPOSTがあったときの処理
# @app.route("/callback", methods=["POST"])
# def callback():
#     # get X-Line-Signature header value
#     signature = request.headers["X-Line-Signature"]
#     # get request body as text
#     body = request.get_data(as_text=True)
#     app.logger.info("Request body: " + body)
#     # handle webhook body
#     try:
#         handler.handle(body, signature)
#     except InvalidSignatureError:
#         abort(400)
#     return "OK"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


# LINE Bot Events
@handler.add(FollowEvent)
def handle_follow(event):
    profile = line_bot_api.get_profile(event.source.user_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            conn.autocommit = True
            cur.execute('CREATE TABLE IF NOT EXISTS users(user_id TEXT)')
            cur.execute('INSERT INTO users (user_id) VALUES (%s)', [profile.user_id])
            print('userIdの挿入OK!!')
            cur.execute('SELECT * FROM users')
            db = cur.fetchall()
    print("< データベース一覧 >")
    for db_check in db:
        print(db_check)


@handler.add(UnfollowEvent)
def handle_unfollow(event):
    with get_connection() as conn:
        with conn.cursor() as cur:
            conn.autocommit = True
            cur.execute('DELETE FROM users WHERE user_id = %s', [event.source.user_id])
    print("userIdの削除OK!!")


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global CODE
    received_text = event.message.text

    if received_text.isdigit() and len(received_text) == 4:
        CODE = received_text
        reply_text = "本当に追加しますか？"
    elif received_text == "":
        received_text = event.message.text
        reply_text = "証券コードを入力してください"
    elif received_text == "yes":
        if len(CODE) == 4:
            output = get_settle_info(CODE) 
            result = transform_style(output)
            save_file(result, output_path)
            read_schedule()
            main()
            reply_text = "カレンダーに追加しました"
        else:
            reply_text = "証券コードが正しくありません。4桁の数字を入力してください。"
    else:
        reply_text = "入力が不明です"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

    print("返信完了!!\ntext:", received_text)


# Main
if __name__ == "__main__":
    with get_connection() as conn:
        with conn.cursor() as cur:
            conn.autocommit = True
            cur.execute('CREATE TABLE IF NOT EXISTS users(user_id TEXT)')

    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
    handle_message()
