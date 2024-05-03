from flask import Flask, request

# 載入 LINE Message API 相關函式庫
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, StickerSendMessage, ImageSendMessage, LocationSendMessage

import json
app = Flask(__name__)


@app.route("/", methods=['POST'])
def linebot():
    body = request.get_data(as_text=True)                 # 取得收到的訊息內容
    try:
        line_bot_api = LineBotApi('5P7RUl8NwthjuSPZvo8eGR0XNToFXesvPkBcJdpmvHab2pgus1PenUaO43WfO4U+hO/tzsLZHm+h+dpayZ5cwVh4XwBS+OZeB/lGwSxpoP04000GM4FcdU6553pPue5KGa/HIqybLn/OcSA/wNEfxgdB04t89/1O/w1cDnyilFU=')     # 確認 token 是否正確
        handler = WebhookHandler('82834ecbcd9989b5e1723a193c85ee72')    # 確認 secret 是否正確
        signature = request.headers['X-Line-Signature']   # 加入回傳的 headers
        handler.handle(body, signature)      # 綁定訊息回傳的相關資訊
        json_data = json.loads(body)         # 轉換內容為 json 格式
        print(json_data)                     # 印出內容
    except:
        print(body)             # 如果發生錯誤，印出收到的內容
    return 'OK'                 # 驗證 Webhook 使用，不能省略
if __name__ == "__main__":
    app.run()
