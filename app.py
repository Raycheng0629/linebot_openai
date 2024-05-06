from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

import requests

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# Function to fetch earthquake information
def earth_quake():
    result = []
    code = 'CWA-B683EE16-4F0D-4C8F-A2AB-CCCA415C60E1'
    try:
        url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0016-001?Authorization={code}'
        req1 = requests.get(url)
        data1 = req1.json()
        eq1 = data1['records']['Earthquake'][0]
        t1 = data1['records']['Earthquake'][0]['EarthquakeInfo']['OriginTime']

        url2 = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0015-001?Authorization={code}'
        req2 = requests.get(url2)
        data2 = req2.json()
        eq2 = data2['records']['Earthquake'][0]
        t2 = data2['records']['Earthquake'][0]['EarthquakeInfo']['OriginTime']

        result = [eq1['ReportContent'], eq1['ReportImageURI']]
        if t2 > t1:
            result = [eq2['ReportContent'], eq2['ReportImageURI']]
    except Exception as e:
        print(e)
        result = ['Failed to fetch data...', '']
    return result

# Function to fetch weather information
def weather(address):
    # Weather fetching logic
    # Replace with your implementation
    pass

# Function to fetch CCTV information
def cctv(msg):
    # CCTV fetching logic
    # Replace with your implementation
    pass

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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    if message == '地震':
        reply = earth_quake()
        text_message = TextSendMessage(text=reply[0])
        line_bot_api.reply_message(event.reply_token, text_message)
        line_bot_api.push_message(event.source.user_id, ImageSendMessage(original_content_url=reply[1], preview_image_url=reply[1]))
    elif message == '天氣':
        address = "Taipei City"
        reply = weather(address)
        text_message = TextSendMessage(text=reply)
        line_bot_api.reply_message(event.reply_token, text_message)
    elif message == 'CCTV':
        msg = "夢時代"
        reply = cctv(msg)
        text_message = TextSendMessage(text=reply)
        line_bot_api.reply_message(event.reply_token, text_message)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)






