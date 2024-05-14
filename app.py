from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, LocationMessage
import requests
import time
import os
import googlemaps

app = Flask(__name__)

# Initialize Google Maps API client
gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))

# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

def forecast(address):
    api_list = {
        "宜蘭縣": "F-D0047-001", "桃園市": "F-D0047-005", "新竹縣": "F-D0047-009", "苗栗縣": "F-D0047-013",
        "彰化縣": "F-D0047-017", "南投縣": "F-D0047-021", "雲林縣": "F-D0047-025", "嘉義縣": "F-D0047-029",
        "屏東縣": "F-D0047-033", "臺東縣": "F-D0047-037", "花蓮縣": "F-D0047-041", "澎湖縣": "F-D0047-045",
        "基隆市": "F-D0047-049", "新竹市": "F-D0047-053", "嘉義市": "F-D0047-057", "臺北市": "F-D0047-061",
        "高雄市": "F-D0047-065", "新北市": "F-D0047-069", "臺中市": "F-D0047-073", "臺南市": "F-D0047-077",
        "連江縣": "F-D0047-081", "金門縣": "F-D0047-085"
    }
    city_id = None
    for name in api_list:
        if name in address:
            city_id = api_list[name]
            break
    if city_id is None:
        return {"Error": "找不到對應的城市代碼"}

    result = {}
    code = 'CWA-B683EE16-4F0D-4C8F-A2AB-CCCA415C60E1'
    t = time.time()
    t1 = time.localtime(t + 28800)
    t2 = time.localtime(t + 28800 + 10800)
    now = time.strftime('%Y-%m-%dT%H:%M:%S', t1)
    now2 = time.strftime('%Y-%m-%dT%H:%M:%S', t2)
    url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/{city_id}?Authorization={code}&elementName=WeatherDescription&timeFrom={now}&timeTo={now2}'
    req = requests.get(url)
    data = req.json()
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

# 處理位置訊息事件
@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    latitude = event.message.latitude
    longitude = event.message.longitude
    # 使用 Google Maps API 將經緯度轉換為地址資訊
    geocode_result = gmaps.reverse_geocode((latitude, longitude), language='zh-TW')
    address = geocode_result[0]['formatted_address']
    # 呼叫 forecast 函式取得天氣預報資料
    weather_forecast = forecast(address)
    # 將天氣預報資料整理成字串
    forecast_str = "\n".join([f"{area}: {note}" for area, note in weather_forecast.items()])
    # 將天氣預報資料以文字訊息回傳給使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=forecast_str)
    )

# 處理文字訊息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if "天氣預報" in event.message.text:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請傳送你所在的位置")
        )
    else:
        location = event.message.text
        weather_forecast = forecast(location)
        if "Error" in weather_forecast:
            reply_message = weather_forecast["Error"]
        else:
            reply_message = "\n".join([f"{area}: {note}" for area, note in weather_forecast.items()])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message)
        )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
