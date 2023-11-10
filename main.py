from __future__ import print_function
from flask import Flask, request, abort
import requests, os
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage,  FollowEvent, UnfollowEvent
import psycopg2
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from bs4 import BeautifulSoup
import re
import logging



# サンプルコードの11~14行目を以下のように書き換え
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
DATABASE_URL = os.environ["DATABASE_URL"]
HEROKU_APP_NAME = os.environ["HEROKU_APP_NAME"]
# LINE_CHANNEL_ACCESS_TOKEN = "jBt7isMYFvFpW8Xw7CGaZXg8W/IyI+5q17yF+mk3PZxuvCCuju9JKy0GYrSnc1HLSf1zXvrEEfEhjqqK8lf0AG+r/NK4kk7qWtjDLE+o8YXfD9dpXbrKOXtZBRuCNuLAEJPnvBCCihJjowH+joxUhQdB04t89/1O/w1cDnyilFU="
# LINE_CHANNEL_SECRET = "4df323f1a72448fd99f5f1587d936001"
# DATABASE_URL = "postgres://ukkvjbsyupdoau:753eed248f3b1e40fd497edd77e76b7159e2d946e8307ab8bfcf90ab1c80184c@ec2-54-156-8-21.compute-1.amazonaws.com:5432/d57qcmlos2bntq"
# HEROKU_APP_NAME = "stock-calander"


app = Flask(__name__)
Heroku = "https://{}-d52dab965779.herokuapp.com/".format(HEROKU_APP_NAME)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

header = {
    "Content_Type": "application/json",
    "Authorization": "Bearer " + LINE_CHANNEL_ACCESS_TOKEN
}


@app.route("/")
def hello_world():
    return "hello world!"


# アプリにPOSTがあったときの処理
@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"




# データベース接続
def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


# botがフォローされたときの処理
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


# botがアンフォロー(ブロック)されたときの処理
@handler.add(UnfollowEvent)
def handle_unfollow(event):
    with get_connection() as conn:
        with conn.cursor() as cur:
            conn.autocommit = True
            cur.execute('DELETE FROM users WHERE user_id = %s', [event.source.user_id])
    print("userIdの削除OK!!")


# ここから追加する
source = 'https://kabuyoho.ifis.co.jp/index.php?action=tp1&sa=report_top&bcode='
CODE = "6758"


# 決算日取得関数 
def get_settleInfo(CODE):
    # クローリング
    try:
        logging.debug('read web data cord = ' + CODE)  # logging
        r = requests.get(source + CODE)
        
    except ValueError:
        logging.debug('read web data ---> Exception Error')  # vlogging
        return None, 'Exception error: access failed'
    
    # スクレイピング
    soup = BeautifulSoup(r.content, "html.parser")
    settleInfo = soup.find("div", class_="header_main").text
    settleInfo = re.sub(r'[\n\t]+', ',', settleInfo)  # メタ文字の除去
    settleInfo = re.sub(r'(^,)|(,$)', '', settleInfo)  # 行頭行末のカンマ除去
    settleInfo = re.sub(r'[\xc2\xa0]', '', settleInfo)  # &nbsp(\xc2\xa0)問題の処置
    logging.debug('settleInfo result = ' + settleInfo)  # logging

    if not settleInfo:
        settleInfo = 'not found'

    return settleInfo


# できすと形式の変更
def transformStyle(inputText):
    parts = inputText.split(',')
    date = parts[7].strip()
    dateParts = date.split('/')
    if len(dateParts) != 3:
        return "日付の形式が正しくありません。"
    formattedDate = f"{dateParts[0]}.{dateParts[1]}"
    title = parts[1].strip()
    quarter = parts[5].strip()
    result = f"{formattedDate}\n{dateParts[2]} {title} {quarter}決算発表"
    return result


# ファイルへの保存
def saveFile(result):
    output = get_settleInfo(CODE)
    result = transformStyle(output)
    with open('output.txt', 'w') as f:
        f.write(result)


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']


# ここのテキストファイルを編集すればおk
def readSchedule():
    f = open('output.txt')
    data1 = f.read()  
    lines1 = data1.split('\n') 
    f.close()
    return lines1


def main():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: 
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    readSchedule()
    print(readSchedule())

    yearmon = readSchedule()[0]
    a = yearmon.split(".")
    year = int(a[0])
    mon = int(a[1])

    if mon == 1 or mon == 3 or mon == 5 or mon == 7 or mon == 8 or mon == 10 or mon == 12:
        num_days = 31
    elif mon == 2:
        num_days = 28
    else:
        num_days = 30
    for i in readSchedule():
        s = i.split(' ')
        if (len(s) == 1):
            continue
        
        d_s = int(s[0])
        d_e = int(s[0])
        m_s = mon
        m_e = mon
        y_s = year
        y_e = year

        if (mon == 12 and d_e == 31):
            y_e = year + 1
        if (num_days == d_e):
            d_e = 1
            if mon == 12:
                m_e = 1
            else:
                m_e = m_e + 1

        event = {
            'summary': '{}'.format(s[1]),
            'location': 'Japan',
            'description': '{}'.format(s[2]),
            'start': {
                'date': '{}-{}-{}'.format(y_s, m_s, d_s),
                'timeZone': 'Japan',
            },
            'end': {
                'date': '{}-{}-{}'.format(y_e, m_e, d_e),
                'timeZone': 'Japan',
            },
        }
        event = service.events().insert(calendarId='maiko02626@gmail.com',
                                        body=event).execute()
        print(event['id'])




# botにメッセージを送ったときの処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    received_text = event.message.text
    
    # Call the function with the received text as an argument
    output = get_settleInfo(received_text)
    
    # Transform the style  ここかも？？？？？
    result = transformStyle(output)
    
    # # Save the result to a file
    saveFile(result)

    # # Call the main function
    main()

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))
    print("返信完了!!\ntext:", event.message.text)
    
    
# アプリの起動
if __name__ == "__main__":
    # 初回のみデータベースのテーブル作成
    with get_connection() as conn:
        with conn.cursor() as cur:
            conn.autocommit = True
            cur.execute('CREATE TABLE IF NOT EXISTS users(user_id TEXT)')
    
    # LINE botをフォローしているアカウントのうちランダムで一人にプッシュ通知
    #push()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
    handle_message()
### End