
# from flask import Flask, request, abort
# import requests, os
# from linebot import LineBotApi, WebhookHandler
# from linebot.exceptions import InvalidSignatureError
# from linebot.models import MessageEvent, TextMessage, TextSendMessage,  FollowEvent, UnfollowEvent
# import psycopg2
# from add_calander import get_settleInfo, transformStyle, saveFile, readSchedule, main


# # サンプルコードの11~14行目を以下のように書き換え
# LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
# LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
# DATABASE_URL = os.environ["DATABASE_URL"]
# HEROKU_APP_NAME = os.environ["HEROKU_APP_NAME"]

# # スクリプトのディレクトリを取得 パスを指定hしないとファイルが生成されなかった
# script_dir = os.path.dirname(os.path.abspath(__file__))
# output_path = os.path.join(script_dir, 'output.txt')   

# app = Flask(__name__)
# Heroku = "https://{}-d52dab965779.herokuapp.com/".format(HEROKU_APP_NAME)

# line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
# handler = WebhookHandler(LINE_CHANNEL_SECRET)

# header = {
#     "Content_Type": "application/json",
#     "Authorization": "Bearer " + LINE_CHANNEL_ACCESS_TOKEN
# }
  

# @app.route("/")
# def hello_world():
#     return "hello world!"


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


# # データベース接続
# def get_connection():
#     return psycopg2.connect(DATABASE_URL, sslmode="require")


# # botがフォローされたときの処理
# @handler.add(FollowEvent)
# def handle_follow(event):
#     profile = line_bot_api.get_profile(event.source.user_id)
#     with get_connection() as conn:
#         with conn.cursor() as cur:
#             conn.autocommit = True
#             cur.execute('CREATE TABLE IF NOT EXISTS users(user_id TEXT)')
#             cur.execute('INSERT INTO users (user_id) VALUES (%s)', [profile.user_id])
#             print('userIdの挿入OK!!')
#             cur.execute('SELECT * FROM users')
#             db = cur.fetchall()
#     print("< データベース一覧 >")
#     for db_check in db:
#         print(db_check)


# # botがアンフォロー(ブロック)されたときの処理
# @handler.add(UnfollowEvent)
# def handle_unfollow(event):
#     with get_connection() as conn:
#         with conn.cursor() as cur:
#             conn.autocommit = True
#             cur.execute('DELETE FROM users WHERE user_id = %s', [event.source.user_id])
#     print("userIdの削除OK!!")


# # If modifying these scopes, delete the file token.pickle.
# SCOPES = ['https://www.googleapis.com/auth/calendar']


# # botにメッセージを送ったときの処理, この関数の中身ごと変える必要があるのでは
# @handler.add(MessageEvent, message=TextMessage)
# def handle_message(event):
#     received_text = event.message.text
#     output = get_settleInfo(received_text) 
#     #エラーはここで検知
#     result = transformStyle(output)
#     saveFile(result, output_path)

#     readSchedule()
#     main()
#     line_bot_api.reply_message(
#         event.reply_token,
#         TextSendMessage(text=event.message.text))
#     print("返信完了!!\ntext:", event.message.text)


# # newversion
# # @handler.add(MessageEvent, message=TextMessage)
# # def handle_message(event):
# #     #ここでメッセージをテキストに入れる
# #     received_text = event.message.text
# #     #カレンダーに追加するのは、４桁の数字が入力された時のみ、それ以外は誘導する
# #     if received_text == "accounts":
# #         line_bot_api.reply_message(
# #             event.reply_token,
# #             TextSendMessage(text="please enter the code of stock brand"))
# #         print("返信完了!!\ntext:", event.message.text)
# #         return
# #     elif received_text == "yes":  
# #         # output = get_settleInfo(received_text)
# #         # result = transformStyle(output)
# #         # saveFile(result, received_text)
# #         # main()
# #         #正しいコードが読み込まれたとき
# #         line_bot_api.reply_message(
# #             event.reply_token,
# #             TextSendMessage(text="カレンダーに追加しました"))
# #         print("返信完了!!\ntext:", event.message.text)

# #     #正しいコードが入力されたとき
# #     else:  
# #         line_bot_api.reply_message(
# #             event.reply_token,
# #             TextSendMessage(text="決算日は　日です、カレンダーに追加しますか"))
# #         print("返信完了!!\ntext:", event.message.text)
# #         return
# #     output = get_settleInfo(received_text)
# #     result = transformStyle(output)
# #     saveFile(result, received_text)
# #     main()

 
# # アプリの起動
# if  __name__ == "__main__":
#     # 初回のみデータベースのテーブル作成
#     with get_connection() as conn:
#         with conn.cursor() as cur:
#             conn.autocommit = True
#             cur.execute('CREATE TABLE IF NOT EXISTS users(user_id TEXT)')
    
#     port = int(os.getenv("PORT", 5000))
#     app.run(host="0.0.0.0", port=port, debug=True)
#     handle_message()
