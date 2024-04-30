from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

import os
import requests
from bs4 import BeautifulSoup
import traceback

app = Flask(__name__)

# LINE Bot 設定
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 開啟 LINE Bot callback
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 定義網路爬蟲函式
def crawl_weather_data(reply_token):
    url = "https://www.ptt.cc/bbs/movie/index.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.find_all("div", class_="title")
    response_message = ""
    for article in articles:
        title = article.text.strip()
        response_message += f"{title}\n"
    line_bot_api.reply_message(reply_token, TextSendMessage(response_message))

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    try:
        if msg == '爬蟲':
            crawl_weather_data(event.reply_token)
        else:
            response = openai.Completion.create(model="gpt-3.5-turbo-instruct", prompt=msg, temperature=0.5, max_tokens=500)
            answer = response['choices'][0]['text'].replace('。','')
            line_bot_api.reply_message(event.reply_token, TextSendMessage(answer))
    except Exception as e:
        print(traceback.format_exc())
        line_bot_api.reply_message(event.reply_token, TextSendMessage('發生錯誤'))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
