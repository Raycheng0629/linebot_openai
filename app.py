from flask import Flask, request, abort
import math, json, time, requests
import os
import googlemaps
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, LocationMessage
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from linebot.models import QuickReply, QuickReplyButton, MessageAction


app = Flask(__name__)

# Initialize Google Maps API client
gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))

# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

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
        result = ['地震資訊取得失敗', '']
    return result

def weather(address):
    result = {}
    code = 'CWA-B683EE16-4F0D-4C8F-A2AB-CCCA415C60E1'
    # 即時天氣
    try:
        url = [
            f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization={code}',
            f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={code}'
        ]
        for item in url:
            req = requests.get(item)
            data = req.json()
            station = data['records']['Station']
            for i in station:
                city = i['GeoInfo']['CountyName']
                area = i['GeoInfo']['TownName']
                if not f'{city}{area}' in result:
                    weather = i['WeatherElement']['Weather']
                    temp = i['WeatherElement']['AirTemperature']
                    humid = i['WeatherElement']['RelativeHumidity']
                    result[f'{city}{area}'] = f'目前天氣狀況「{weather}」，溫度 {temp} 度，相對濕度 {humid}%！'
    except Exception as e:
        print(e)

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
    if not city_id:
        return '找不到氣象資訊'

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
    for item in location:
        try:
            area = item['locationName']
            note = item['weatherElement'][0]['time'][0]['elementValue'][0]['value']
            if not f'{city}{area}' in result:
                result[f'{city}{area}'] = ''
            else:
                result[f'{city}{area}'] += '。\n\n'
            result[f'{city}{area}'] += '未來三小時' + note
        except Exception as e:
            print(e)

    try:
        url = 'https://data.moenv.gov.tw/api/v2/aqx_p_432?api_key=e8dd42e6-9b8b-43f8-991e-b3dee723a52d&limit=1000&sort=ImportDate%20desc&format=JSON'
        req = requests.get(url)
        data = req.json()
        records = data['records']
        aqi_status = ['良好', '普通', '對敏感族群不健康', '對所有族群不健康', '非常不健康', '危害']
        for item in records:
            county = item['county']
            sitename = item['sitename']
            name = f'{county}{sitename}'
            aqi = int(item['aqi'])
            msg = aqi_status[aqi // 50]

            for k in result:
                if name in k:
                    result[k] += f'\n\nAQI：{aqi}，空氣品質{msg}。'
    except Exception as e:
        print(e)

    for i in result:
        if i in address:
            output = f'「{address}」{result[i]}'
            break
    return output

def get_news():
    url = "https://udn.com/news/breaknews/1"
    response = requests.get(url)
    response.encoding = 'utf-8'  # 設定編碼避免亂碼

    news_list = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        container_elements = soup.find_all(class_='story-list__text')
        for container_element in container_elements:
            try:
                link_elements = container_element.find_all('a')
                for link_element in link_elements:
                    link_text = link_element.get_text(strip=True)
                    link_url = link_element['href']
                    absolute_link_url = urljoin(url, link_url)  # 轉換為絕對路徑
                    news_list.append({
                        'title': link_text,
                        'url': absolute_link_url
                    })
            except Exception as e:
                print("連結提取失敗:", str(e))
        
        return news_list
    else:
        print("無法取得網頁內容，狀態碼:", response.status_code)
        return []

@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_data(as_text=True)
    try:
        signature = request.headers['X-Line-Signature']
        handler.handle(body, signature)
        json_data = json.loads(body)
        reply_token = json_data['events'][0]['replyToken']
        user_id = json_data['events'][0]['source']['userId']
        print(json_data)
        type = json_data['events'][0]['message']['type']
        if type == 'text':
            text = json_data['events'][0]['message']['text']
            if text == '雷達回波圖' or text == '雷達回波':
                img_url = f'https://cwaopendata.s3.ap-northeast-1.amazonaws.com/Observation/O-A0058-001.png?{time.time_ns()}'
                img_message = ImageSendMessage(original_content_url=img_url, preview_image_url=img_url)
                line_bot_api.reply_message(reply_token, img_message)
            elif text == '即時新聞':
                news_data = get_news()
                news_message = "\n\n".join([f"標題: {news['title']}\n網址: {news['url']}" for news in news_data])
                line_bot_api.reply_message(reply_token, TextSendMessage(text=news_message))
        elif type == 'location':
            address = json_data['events'][0]['message']['address'].replace('台', '臺')
            reply = weather(address)
            text_message = TextSendMessage(text=reply)
            line_bot_api.reply_message(reply_token, text_message)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        print(e)
    return 'OK'

@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    latitude = event.message.latitude
    longitude = event.message.longitude
    geocode_result = gmaps.reverse_geocode((latitude, longitude), language='zh-TW')
    address = geocode_result[0]['formatted_address'].replace('台', '臺')
    weather_forecast = weather(address)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=weather_forecast)
    )

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    if "天氣預報" in message:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請傳送你所在的位置")
        )
    elif message == '今日運勢':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(
            text='請選擇你那邊的天氣狀況',
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(action=MessageAction(label='晴天', text='晴天')),
                    QuickReplyButton(action=MessageAction(label='晴時多雲', text='晴時多雲')),
                    QuickReplyButton(action=MessageAction(label='雨天', text='雨天')),
                    QuickReplyButton(action=MessageAction(label='陰天', text='陰天')),
                    QuickReplyButton(action=MessageAction(label='多雲', text='多雲'))
                ]
            )
        ))
    elif message in ['晴天', '晴時多雲', '雨天', '陰天', '多雲']:
        weather_info = message
        fortune = choose_fortune(weather_info)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=fortune))
    elif message == '地震':
        reply = earth_quake()
        text_message = TextSendMessage(text=reply[0])
        line_bot_api.reply_message(event.reply_token, text_message)
        line_bot_api.push_message(event.source.user_id, ImageSendMessage(original_content_url=reply[1], preview_image_url=reply[1]))


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
