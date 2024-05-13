from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, LocationMessage
import requests
import os
import googlemaps

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
 
google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(key=google_maps_api_key)

def forecast(address):
    api_list = {"宜蘭縣":"F-D0047-001","桃園市":"F-D0047-005","新竹縣":"F-D0047-009","苗栗縣":"F-D0047-013",
            "彰化縣":"F-D0047-017","南投縣":"F-D0047-021","雲林縣":"F-D0047-025","嘉義縣":"F-D0047-029",
            "屏東縣":"F-D0047-033","臺東縣":"F-D0047-037","花蓮縣":"F-D0047-041","澎湖縣":"F-D0047-045",
            "基隆市":"F-D0047-049","新竹市":"F-D0047-053","嘉義市":"F-D0047-057","臺北市":"F-D0047-061",
            "高雄市":"F-D0047-065","新北市":"F-D0047-069","臺中市":"F-D0047-073","臺南市":"F-D0047-077",
            "連江縣":"F-D0047-081","金門縣":"F-D0047-085"}
    for name in api_list:
        if name in address:
            city_id = api_list[name]
    result = {}
    code = 'CWA-B683EE16-4F0D-4C8F-A2AB-CCCA415C60E1'
    t = time.time()
    t1 = time.localtime(t+28800)
    t2 = time.localtime(t+28800+10800)
    now = time.strftime('%Y-%m-%dT%H:%M:%S',t1)
    now2 = time.strftime('%Y-%m-%dT%H:%M:%S',t2)
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

# 處理文字訊息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if "天氣預報" in event.message.text:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請告訴我您所在的位置，例如：臺北市、新北市、高雄市等。")
        ) 
    else:
        location = event.message.text
        weather_forecast = forecast(location)
        reply_message = "\n".join([f"{area}: {note}" for area, note in weather_forecast.items()])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message)
        )

# 處理位置訊息事件
@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    latitude = event.message.latitude
    longitude = event.message.longitude
    if latitude is None or longitude is None:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="無法取得位置資訊")
        )
        return
    # 使用 Google Maps API 將經緯度轉換為地址資訊
    geocode_result = gmaps.reverse_geocode((latitude, longitude))
    address = geocode_result[0]['formatted_address']
    # 將地址資訊作為參數傳遞給 forecast 函式進行天氣預報
    weather_forecast = forecast(address)
    reply_message = "\n".join([f"{area}: {note}" for area, note in weather_forecast.items()])
    # 回傳天氣預報訊息給使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
