from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#======python的函數庫==========
import tempfile, os
import datetime
import openai
import time
import traceback
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')


def GPT_response(text):
    # 接收回應
    response = openai.Completion.create(model="gpt-3.5-turbo-instruct", prompt=text, temperature=0.5, max_tokens=500)
    print(response)
    # 重組回應
    answer = response['choices'][0]['text'].replace('。','')
    return answer


# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    try:
        GPT_answer = GPT_response(msg)
        print(GPT_answer)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))
    except:
        print(traceback.format_exc())
        line_bot_api.reply_message(event.reply_token, TextSendMessage('你所使用的OPENAI API key額度可能已經超過，請於後台Log內確認錯誤訊息'))
        

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)


@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)
    
#--------------
@handler.add(MessageEvent, message=TextMessage)
# 引入必要的函式庫
import requests
from bs4 import BeautifulSoup

# 定義網路爬蟲函式
def crawl_weather_data(reply_token):
    # PTT 電影版的網址
    url = "https://www.ptt.cc/bbs/movie/index.html"
    
    # 發送 GET 請求獲取網頁內容
    response = requests.get(url)
    
    # 使用 BeautifulSoup 解析網頁內容
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 找到所有文章標題的元素
    articles = soup.find_all("div", class_="title")
    
    # 初始化回應訊息
    response_message = ""
    
    # 提取文章標題並組合成回應訊息
    for article in articles:
        title = article.text.strip()  # 去除空白字符
        response_message += f"{title}\n"
    
    # 回覆訊息給使用者
    line_bot_api.reply_message(reply_token, TextSendMessage(response_message))


# 在 handle_message 函式中加入對「爬蟲」訊息的處理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    if msg == '爬蟲':
        crawl_weather_data(event.reply_token)
    else:
        try:
            GPT_answer = GPT_response(msg)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))
        except:
            print(traceback.format_exc())
            line_bot_api.reply_message(event.reply_token, TextSendMessage('發生錯誤'))



#-----------------
        
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
