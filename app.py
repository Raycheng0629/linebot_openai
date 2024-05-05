from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

import os

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

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

# 記錄使用者輸入的天氣狀況
user_weather = {}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.lower()  # 將用戶訊息轉換成小寫，以便比較
    if user_id not in user_weather:  # 如果使用者尚未輸入過天氣狀況
        user_weather[user_id] = user_message
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="你那邊天氣如何? 分別有晴天、晴時多雲、雨天、陰天、多雲")
        )
    else:  # 如果使用者已經輸入過天氣狀況
        weather_responses = {
            '晴天': '陽光明媚，心情愉悅，今天適合外出活動，盡情享受陽光的溫暖。去運動、旅行或與好友聚會，你會充滿活力和快樂。',
            '晴時多雲': '雖然天空中偶爾會出現雲彩，但整體來說還是個不錯的天氣。趁著陽光，做些你喜歡的事情吧！',
            '雨天': '今天下雨了，記得攜帶雨具，小心別淋濕了。不過，也是個適合宅在家裡，享受悠閒時光的好日子。',
            '陰天': '天空灰蒙蒙的，有點陰沉。這種天氣最適合泡一杯熱茶，靜靜地坐在窗邊看書。',
            '多雲': '雲層密佈整個天空，感覺有點涼。不過別擔心，多雲的天氣也很適合出門散步，享受大自然的美景。'
        }
        if user_message in weather_responses:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=weather_responses[user_message])
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="你那邊天氣如何? 分別有晴天、晴時多雲、雨天、陰天、多雲")
            )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
