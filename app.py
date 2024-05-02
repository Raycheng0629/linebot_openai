from flask import Flask, request, abort
import json

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

file_path = r"/content/F-C0032-001.json"

with open(file_path, 'r') as file:
    data_json = json.load(file)

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
        city_data = find_city_data(msg)
        if city_data:
            reply_message = generate_weather_response(city_data)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(reply_message))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("抱歉，找不到該城市的天氣資訊。"))
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage('處理訊息時發生錯誤。'))
# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    if msg in ["台北", "新北", "桃園", "台中", "台南", "高雄"]:  # 在這裡列出你希望觸發天氣查詢的城市名稱
        try:
            city_data = find_city_data(msg)
            if city_data:
                reply_message = generate_weather_response(city_data)
                line_bot_api.reply_message(event.reply_token, TextSendMessage(reply_message))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage("抱歉，找不到該城市的天氣資訊。"))
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('處理訊息時發生錯誤。'))

def find_city_data(city_name):
    for location in data_json['cwaopendata']['dataset']['location']:
        if location['locationName'] == city_name:
            return location
    return None

def generate_weather_response(city_data):
    wx8 = city_data['weatherElement'][0]['time'][0]['parameter']['parameterName']    # 天氣現象
    maxt8 = city_data['weatherElement'][1]['time'][0]['parameter']['parameterName']  # 最高溫
    mint8 = city_data['weatherElement'][2]['time'][0]['parameter']['parameterName']  # 最低溫
    pop8 = city_data['weatherElement'][4]['time'][0]['parameter']['parameterName']   # 降雨機率
    reply_message = f"{city_data['locationName']}未來 8 小時{wx8}，最高溫 {maxt8} 度，最低溫 {mint8} 度，降雨機率 {pop8} %"
    return reply_message

@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)
        
        
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


