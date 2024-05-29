from flask import Flask, request, abort
import os
import time
import json
import requests
import googlemaps
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, LocationMessage, QuickReply, QuickReplyButton, MessageAction, TemplateSendMessage, ButtonsTemplate, URITemplateAction

app = Flask(__name__)

# Initialize Google Maps API client
gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))

# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

news_categories = {
    "精選": "https://udn.com/news/breaknews/1",
    "財經": "https://udn.com/news/breaknews/1/6#breaknews",
    "股市": "https://udn.com/news/breaknews/1/11#breaknews",
    "科技": "https://udn.com/news/breaknews/1/13#breaknews",
    "娛樂": "https://udn.com/news/breaknews/1/8#breaknews",
    "社會": "https://udn.com/news/breaknews/1/2#breaknews",
    "氣象新聞": "https://udn.com/search/tagging/2/%E6%A5%B5%E7%AB%AF%E6%B0%A3%E5%80%99"
}

def get_news(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
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
                    absolute_link_url = urljoin(url, link_url)
                    news_list.append({'title': link_text, 'url': absolute_link_url})
            except Exception as e:
                print("連結提取失敗:", str(e))
        return news_list
    else:
        print("無法取得網頁內容，狀態碼:", response.status_code)
        return []

def earth_quake():
    result = []
    code = 'CWA-B683EE16-4F0D-4C8F-A2AB-CCCA415C60E1'
    try:
        url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0016-001?Authorization={code}'
        req1 = requests.get(url)
        data1 = req1.json()
        eq1 = data1['records']['Earthquake'][0]
        t1 = eq1['EarthquakeInfo']['OriginTime']

        url2 = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0015-001?Authorization={code}'
        req2 = requests.get(url2)
        data2 = req2.json()
        eq2 = data2['records']['Earthquake'][0]
        t2 = eq2['EarthquakeInfo']['OriginTime']

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
                    temp = float(i['WeatherElement']['AirTemperature'])
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
            weather_info = result[i]
            temp = float(weather_info.split("溫度 ")[1].split(" 度")[0])
            rain_prob = float(weather_info.split("降雨機率 ")[1].split("%")[0])
            aqi = int(weather_info.split("AQI：")[1].split("，")[0]) if "AQI：" in weather_info else 0
            health_advice = generate_health_advice(temp, rain_prob, aqi)
            return weather_info + '\n\n' + health_advice
    return '找不到氣象資訊'

def generate_health_advice(temp, rain_prob, aqi):
    advice = []

    # Temperature advice
    if temp >= 30:
        advice.append("天氣炎熱，請注意防曬並補充水分。")
    elif temp <= 10:
        advice.append("天氣寒冷，請穿著保暖衣物。")

    # Rain probability advice
    if rain_prob >= 50:
        advice.append("降雨機率高，出門請攜帶雨具。")

    # AQI advice
    if aqi >= 101:
        advice.append("空氣品質不佳，敏感族群請減少外出。")
    if aqi >= 151:
        advice.append("空氣品質非常不佳，所有族群請減少外出。")
    if aqi >= 201:
        advice.append("空氣品質危害健康，避免外出。")

    return "\n".join(advice) if advice else "氣象條件良好，無需特別注意。"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text

    if text.startswith("隨便吃"):
        address = text[3:].strip()
        if not address:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入地址或位置"))
        else:
            search_restaurant(event, address)
    elif text in news_categories:
        send_news(event, text)
    elif "氣象" in text:
        location = text.split("氣象")[1].strip()
        weather_info = weather(location)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=weather_info))
    elif "地震" in text:
        eq = earth_quake()
        line_bot_api.reply_message(event.reply_token, [
            TextSendMessage(text=eq[0]),
            ImageSendMessage(original_content_url=eq[1], preview_image_url=eq[1])
        ])
    elif text == '功能':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text='請選擇功能：',
                quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(action=MessageAction(label="地震", text="地震")),
                        QuickReplyButton(action=MessageAction(label="氣象", text="氣象")),
                        QuickReplyButton(action=MessageAction(label="美食", text="隨便吃")),
                        QuickReplyButton(action=MessageAction(label="新聞", text="新聞"))
                    ]
                )
            )
        )

def search_restaurant(event, address):
    try:
        geocode_result = gmaps.geocode(address)
        if not geocode_result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="查無餐廳"))
            return

        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']

        food_store_search = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?key={os.getenv('GOOGLE_MAPS_API_KEY')}&location={lat},{lng}&rankby=distance&type=restaurant&language=zh-TW"
        food_req = requests.get(food_store_search)
        nearby_restaurants_dict = food_req.json()
        top20_restaurants = nearby_restaurants_dict["results"]

        if not top20_restaurants:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="查無餐廳"))
            return

        bravo = [i for i in range(len(top20_restaurants)) if top20_restaurants[i].get('rating', 0) > 3.9]

        if len(bravo) < 8:
            content = "沒找到高評分的店家，隨便選一家"
            restaurant = top20_restaurants[random.choice(range(len(top20_restaurants)))]
        else:
            restaurant = top20_restaurants[random.choice(bravo)]

        photo_reference = restaurant.get("photos", [{}])[0].get("photo_reference")
        photo_width = restaurant.get("photos", [{}])[0].get("width", 0)
        thumbnail_image_url = f"https://maps.googleapis.com/maps/api/place/photo?key={os.getenv('GOOGLE_MAPS_API_KEY')}&photoreference={photo_reference}&maxwidth={photo_width}" if photo_reference else None
        rating = restaurant.get("rating", "無")
        address = restaurant.get("vicinity", "沒有資料")
        details = f"Google Map分數: {rating}\n地址: {address}"
        map_url = f"https://www.google.com/maps/search/?api=1&query={restaurant['geometry']['location']['lat']},{restaurant['geometry']['location']['lng']}&query_place_id={restaurant['place_id']}"

        buttons_template = TemplateSendMessage(
            alt_text=restaurant["name"],
            template=ButtonsTemplate(
                thumbnail_image_url=thumbnail_image_url,
                title=restaurant["name"],
                text=details,
                actions=[URITemplateAction(label='查看地圖', uri=map_url)]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
    except Exception as e:
        print(e)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="出現錯誤，請稍後再試"))

def send_news(event, category):
    url = news_categories[category]
    news = get_news(url)
    if not news:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="目前無法取得新聞，請稍後再試。"))
    else:
        news_texts = [f"{i+1}. {n['title']}\n{n['url']}" for i, n in enumerate(news[:5])]
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="\n\n".join(news_texts)))

if __name__ == "__main__":
    app.run(debug=True)
