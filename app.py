from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, LocationMessage
)
import requests
import time
import os

app = Flask(__name__)

line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_CHANNEL_SECRET')

def forecast(address):
    # 將主要縣市個別的 JSON 代碼列出
    api_list = {"宜蘭縣":"F-D0047-001","桃園市":"F-D0047-005","新竹縣":"F-D0047-009","苗栗縣":"F-D0047-013",
            "彰化縣":"F-D0047-017","南投縣":"F-D0047-021","雲林縣":"F-D0047-025","嘉義縣":"F-D0047-029",
            "屏東縣":"F-D0047-033","臺東縣":"F-D0047-037","花蓮縣":"F-D0047-041","澎湖縣":"F-D0047-045",
            "基隆市":"F-D0047-049","新竹市":"F-D0047-053","嘉義市":"F-D0047-057","臺北市":"F-D0047-061",
            "高雄市":"F-D0047-065","新北市":"F-D0047-069","臺中市":"F-D0047-073","臺南市":"F-D0047-077",
            "連江縣":"F-D0047-081","金門縣":"F-D0047-085"}
    for name in api_list:
        if name in address:
            city_id = api_list[name]   # 根據提供的地址，取得縣市代碼
    result = {}
    code = 'CWA-B683EE16-4F0D-4C8F-A2AB-CCCA415C60E1'
    t = time.time()
    t1 = time.localtime(t)       
    t2 = time.localtime(t+10800) 
    now = time.strftime('%Y-%m-%dT%H:%M:%S',t1)
    now2 = time.strftime('%Y-%m-%dT%H:%M:%S',t2)
    url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/{city_id}?Authorization={code}&elementName=WeatherDescription&timeFrom={now}&timeTo={now2}'
    req = requests.get(url)   # 取得主要縣市預報資料
    data = req.json()         # json 格式化訊息內容
    location = data['records']['locations'][0]['location']
    city = data['records']['locations'][0]['locationsName']
    for i in location:
        area = i['locationName']
        note = i['weatherElement'][0]['time'][0]['elementValue'][0]['value']
        result[f'{city}{area}'] = '未來三小時' + note
    return result

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

@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    latitude = event.message.latitude
    longitude = event.message.longitude
    address = reverse_geocode(latitude, longitude)  # Assuming you have a function to reverse geocode
    result = forecast(address)
    reply_message = "\n".join([f"{area}: {note}" for area, note in result.items()])
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
