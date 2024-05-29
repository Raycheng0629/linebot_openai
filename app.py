#5/28版本 天氣預報 今日運勢 地震 即時新聞 氣象新聞 健康提醒 附近午餐選單 功能已完成
from flask import Flask, request, abort
import os
import json
import requests
import googlemaps
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, LocationMessage,
    QuickReply, QuickReplyButton, MessageAction, ImageCarouselTemplate,
    ImageCarouselColumn, TemplateSendMessage, URIAction,
    ButtonsTemplate, URITemplateAction, CarouselTemplate, CarouselColumn
)


app = Flask(__name__)


# Initialize Google Maps API client
gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))


# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))


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
            health_advice = generate_health_advice(weather_info, temp, rain_prob, aqi)
            output = f'「{address}」{weather_info}\n-------------------------------\n健康提醒：\n{health_advice}'
            break
    return output


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
            elif text in news_categories:
                news_data = get_news(news_categories[text])
                news_message = "\n\n".join([f"{i+1}. {news['title']}\n{news['url']}" for i, news in enumerate(news_data[:5])])
                line_bot_api.reply_message(reply_token, TextSendMessage(text=news_message))
            elif text == '氣象新聞':
                news_data = get_news(news_categories[text])
                news_message = "\n\n".join([f"{i+1}. {news['title']}\n{news['url']}" for i, news in enumerate(news_data[:5])])
                line_bot_api.reply_message(reply_token, TextSendMessage(text=news_message))
            elif text == '即時新聞':
                quick_reply = QuickReply(
                    items=[
                        QuickReplyButton(action=MessageAction(label='精選', text='精選')),
                        QuickReplyButton(action=MessageAction(label='財經', text='財經')),
                        QuickReplyButton(action=MessageAction(label='股市', text='股市')),
                        QuickReplyButton(action=MessageAction(label='娛樂', text='娛樂')),
                        QuickReplyButton(action=MessageAction(label='社會', text='社會')),
                        QuickReplyButton(action=MessageAction(label='科技', text='科技'))
                    ]
                )
                line_bot_api.reply_message(reply_token, TextSendMessage(text="請選擇新聞類別", quick_reply=quick_reply))
            elif text == '健康提醒':
                address = json_data['events'][0]['message']['address'].replace('台', '臺')
                reply = weather(address)
                text_message = TextSendMessage(text=reply)
                line_bot_api.reply_message(reply_token, text_message)
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
            TextSendMessage(text="請傳送你所在的位置資訊")
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
        forecast = choose_fortune(message)  
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=forecast)
        )
    elif message == '地震':
        reply = earth_quake()
        text_message = TextSendMessage(text=reply[0])
        line_bot_api.reply_message(event.reply_token, text_message)
        line_bot_api.push_message(event.source.user_id, ImageSendMessage(original_content_url=reply[1], preview_image_url=reply[1]))
    elif message == '我想找附近美食':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="輸入:我想吃 輸入欲查詢的地址,如:我想吃 台北市士林區臨溪路70號")
        )
         if lineMessage[0:3] == "我想吃":
            lineMes = lineMessage
            if lineMes[4:].strip() == '':
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="查無該地址"))
                return
            else:
                address = lineMes[4:].strip()
            
            addurl = 'https://maps.googleapis.com/maps/api/geocode/json?key={}&address={}&sensor=false'.format(os.getenv('GOOGLE_MAPS_API_KEY'), address)
            addressReq = requests.get(addurl)
            addressDoc = addressReq.json()
            
            if not addressDoc['results']:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="查無地址"))
                return
            
            lat = addressDoc['results'][0]['geometry']['location']['lat']
            lng = addressDoc['results'][0]['geometry']['location']['lng']
            
            foodStoreSearch = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?key={}&location={},{}&rankby=distance&type=restaurant&language=zh-TW".format(os.getenv('GOOGLE_MAPS_API_KEY'), lat, lng)
            foodReq = requests.get(foodStoreSearch)
            nearby_restaurants_dict = foodReq.json()
            top20_restaurants = nearby_restaurants_dict["results"]
            
            if not top20_restaurants:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="查無餐廳"))
                return
            
            bravo = []
            
            for restaurant in top20_restaurants:
                try:
                    if restaurant['rating'] > 3.8:
                        bravo.append(restaurant)
                        if len(bravo) >= 8:
                            break
                except KeyError:
                    continue
            
            if not bravo:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="沒找到高評分的店家，隨便選一家"))
                return
            
            columns = []
            for restaurant in bravo:
                if restaurant.get("photos"):
                    photo_reference = restaurant["photos"][0]["photo_reference"]
                    photo_width = restaurant["photos"][0]["width"]
                    thumbnail_image_url = "https://maps.googleapis.com/maps/api/place/photo?key={}&photoreference={}&maxwidth={}".format(os.getenv('GOOGLE_MAPS_API_KEY'), photo_reference, photo_width)
                else:
                    thumbnail_image_url = None
    
                rating = "無" if restaurant.get("rating") is None else restaurant["rating"]
                address = "沒有資料" if restaurant.get("vicinity") is None else restaurant["vicinity"]
                details = "Google Map分數: {}\n地址: {}".format(rating, address)
                
                map_url = "https://www.google.com/maps/search/?api=1&query={},{}&query_place_id={}".format(
                    restaurant["geometry"]["location"]["lat"],
                    restaurant["geometry"]["location"]["lng"],
                    restaurant["place_id"]
                )
                
                column = CarouselColumn(
                    thumbnail_image_url=thumbnail_image_url,
                    title=restaurant["name"],
                    text=details,
                    actions=[
                        URITemplateAction(
                            label='查看地圖',
                            uri=map_url
                        )
                    ]
                )
                columns.append(column)
            
            carousel_template = TemplateSendMessage(
                alt_text='高評分餐廳',
                template=CarouselTemplate(columns=columns)
            )
            
            line_bot_api.reply_message(event.reply_token, carousel_template)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)



