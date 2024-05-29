#5/28版本 天氣預報 今日運勢 地震 即時新聞 氣象新聞 健康提醒 附近午餐選單 功能已完成
from flask import Flask, request, abort
import os
import json
import requests
import googlemaps
import time
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


def choose_fortune(weather):
    fortunes = {
        '晴天': [
            "☀️ 陽光燦爛，萬物生機勃發!今天適合出去走走,來場說走就走的小旅行吧。🚲🏞️你可以騎自行車遊園地,或者徒步登山呼吸新鮮空氣,活力滿滿!",
            "🌞 烏鴉在樹梢上吱喳歌唱,花兒爭相怒放,這種開朗樂觀的氛圍能感染你的心靈。📚💪趕緊投入工作或學習,收獲累累碩果,展現你的才華吧!",
            "☀️ 金光灑落,希望如潮水般湧來,什麼都有可能發生!😎💬大膽表達自己的想法和願望,相信同路人一定會給你力量和鼓勵。",
            "☀️ 藍天白雲,心情格外舒暢!不如邀上三五好友,來一場輕鬆愉快的聚會吧。🍕🍹美食佳餚加上談天說地,定能讓你快樂回味。",
            "🌈 豔陽高照,你滿懷自信和勇氣。不妨挑戰自我,發掘更強大的自我。💪🎉突破障礙,定能收穫成長與成就感!"
        ],
        '晴時多雲': [
            "⛅ 陽光時隱時現,有如生活的變幻莫測。但別擔心,未來總有驚喜在等著你。🌟💭保持希望,專注於目標,你一定會遇到曙光。",
            "🌤 陽光跟雲彩追逐嬉戲,心情也隨之變幻多端。但只要積極面對,就能順利渡過難關。🔍💼相信自己,堅持下去,你一定能找到成功之路。",
            "⛅ 太陽與雲朵你爭我奪,不禁讓人期待接下來會發生什麼。🌈💫保持開放心態,擁抱生活的變化,你一定會發現美好就在眼前。",
            "🌤 陽光時隱時現,要好好珍惜眼前的一切。💖🌼感恩生活中的每一個小確幸,你的生活必定更加豐富多彩。",
            "⛅ 晴空與烏雲交織,你也感到輕鬆愉悅。👀🌺與親朋好友相聚,一起享受美好時光,定能讓你心情愉悅不已。"
        ],
        '雨天': [
            "🌧 細雨綿綿,如詩如畫,聆聽雨聲,你的心靈會得到淨化和安寧。🎵📖找個安靜角落,沉澱思緒,你一定能找到內心的寧靜。",
            "🌧 雨聲悠悠,彷彿打動心弦。沉澱心靈,你一定能找到平靜與安寧。✍️🌱將內心的想法和感受盡情灑落,你的情緒必將得到抒發。",
            "🌧 雨水滋潤大地,賦予生命嶄新希望。感受雨水的洗禮,你一定會找到全新的生活動力。🌈🌱期待明天會更加美好!",
            "🌦 在雨中漫步,讓雨水洗滌你的塵世疲憊。😌🌧享受雨水帶來的清新和愉悅,你的生活定會因此變得更加美好。",
            "🌧 淅瀝瀝的雨聲,令人神清氣爽。🌂💕與親人分享彼此的感受,定能溫暖你的心房。"
        ],
        '陰天': [
            "☁️ 陰雲密布,心靈變得格外平靜安詳。這正是思考人生的好時機。🧘‍♂️📝找一個靜謐的角落,好好反思人生的意義和方向,定能有所領悟。",
            "☁️ 陰天使人內心澄澈,這正是放鬆思緒的好時機。📚🌌沉浸在一本好書或輕音樂中,你一定能找到心靈的寧靜。",
            "☁️ 陰天雖然暗淡,但也是成長的機會。 勇敢面對挑戰,你一定能蛻變得更加堅強。🔍💪接受生活的考驗,定能收穫成長與喜悅。",
            "☁️ 陰天雖令人沮喪,但陽光總會重現天際。保持樂觀,相信自己和未來,光明就在不遠處。🌅💭",
        ],
        '多雲': [
            "🌥 白雲朵朵,讓人心生期待。這正是探索新事物的好時機。🚀🌌大膽嘗試吧,你一定能豐富自己的生活,獲得全新體驗。",
            "🌥 天空多雲變幻不定,但這正是生活的常態。保持開放心態,你一定能發現美好就在眼前。🎨🌟接受變化,好好享受當下,你定能獲得快樂與滿足。",
            "🌥 陽光時而若隱若現,別讓煩憂擾亂了心情。💖🌟珍惜生活中的每一個小確幸,你的生活一定會更加精彩。",
            "🌥 多雲蒙蒙,令人遐想飛揚。保持好奇心探尋大自然的奧秘,定能有驚喜在等著你!🔍🎉與親朋好友一起探索大自然,定能收穫美好回憶。",
        ]
    }
    return random.choice(fortunes[weather])  # 從指定天氣的運勢結果中隨機選擇一個


news_categories = {
    "精選": "https://udn.com/news/breaknews/1",
    "財經": "https://udn.com/news/breaknews/1/6#breaknews",
    "股市": "https://udn.com/news/breaknews/1/11#breaknews",
    "科技": "https://udn.com/news/breaknews/1/13#breaknews",
    "娛樂": "https://udn.com/news/breaknews/1/8#breaknews",
    "社會": "https://udn.com/news/breaknews/1/2#breaknews",
    "氣象新聞":"https://udn.com/search/tagging/2/%E6%A5%B5%E7%AB%AF%E6%B0%A3%E5%80%99"
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
            health_advice = generate_health_advice(weather_info, temp, rain_prob, aqi)
            output = f'「{address}」{weather_info}\n-------------------------------\n健康提醒：\n{health_advice}'
            break
    return output

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    try:
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
        print("輸入:我想吃 輸入欲查詢的地址,如:我想吃 台北市士林區臨溪路70號")

       
def generate_health_advice(weather_info, temp, rain_prob, aqi):
    advice = []


    # Weather condition advice
    if '晴' in weather_info:
        advice.append("天氣狀況「晴」:\n配件：戴帽子、太陽眼鏡、使用防曬霜。\n活動：避免中午時段在戶外活動，適合晨間和晚間運動。")
    elif '陰' in weather_info:
        advice.append("天氣狀況「陰」:\n配件：攜帶輕便外套或毛衣。\n活動：適合全天候戶外活動，注意天氣變化。")
    elif '多雲' in weather_info:
        advice.append("天氣狀況「多雲」:\n配件：攜帶小型折疊傘，備用雨具。\n活動：適合戶外活動，但要注意雲層變化，隨時準備應對降雨。")
    elif '雨' in weather_info:
        advice.append("天氣狀況「雨」:\n配件：撐傘、穿防水外套或雨衣、穿防滑鞋。\n活動：避免在低窪地區停留，注意行人和交通安全。")


    # Temperature advice
    if temp > 30:
        advice.append(f"溫度 {temp} 度:\n穿著：輕薄、透氣的棉質或亞麻衣物，短袖短褲，涼鞋。\n活動：多喝水，避免烈日下長時間活動，室內保持通風或使用空調。")
    elif 20 <= temp <= 30:
        advice.append(f"溫度 {temp} 度:\n穿著：舒適、透氣的衣物，如 T 恤、薄長褲或裙子，攜帶輕便外套以應對早晚溫差。\n活動：適合各類戶外活動，注意適時補充水分。")
    elif 10 <= temp < 20:
        advice.append(f"溫度 {temp} 度:\n穿著：長袖衣物，薄外套或風衣。\n活動：適合戶外運動，但早晚可能需要加穿外套。")
    elif temp < 10:
        advice.append(f"溫度 {temp} 度:\n穿著：厚重的衣物，如羽絨服、毛衣，戴手套、圍巾、帽子。\n活動：注意保暖，避免長時間在室外，尤其是寒風中。")


    # Rain probability advice
    if rain_prob > 40:
        advice.append(f"降雨機率 {rain_prob}%:\n配件：攜帶雨傘或雨衣，穿防水鞋。\n活動：安排室內活動，外出時注意路面濕滑。")
    elif 20 <= rain_prob <= 40:
        advice.append(f"降雨機率 {rain_prob}%:\n配件：攜帶小型折疊傘，以備不時之需。\n活動：可以進行戶外活動，但要注意天氣變化，避免久留戶外。")
    elif rain_prob < 20:
        advice.append(f"降雨機率 {rain_prob}%:\n配件：不需特別準備，但可注意天氣變化。\n活動：適合各類戶外活動。")


    # AQI advice
    if 0 <= aqi <= 50:
        advice.append(f"AQI 值 {aqi}:\n空氣質量優良，適合所有戶外活動。")
    elif 51 <= aqi <= 100:
        advice.append(f"AQI 值 {aqi}:\n空氣質量尚可，一般人群可以正常活動，敏感人群（如老人、小孩、呼吸道疾病患者）外出時應減少高強度戶外活動。")
    elif 101 <= aqi <= 150:
        advice.append(f"AQI 值 {aqi}:\n敏感人群應減少戶外活動，戴口罩，一般人群注意適當減少高強度戶外活動。")
    elif 151 <= aqi <= 200:
        advice.append(f"AQI 值 {aqi}:\n所有人群應減少戶外活動，建議戴口罩，尤其是在戶外運動時。")
    elif 201 <= aqi <= 300:
        advice.append(f"AQI 值 {aqi}:\n避免外出，尤其是老年人、兒童和有呼吸道疾病的人，必須外出時戴 N95 口罩。")
    elif aqi > 300:
        advice.append(f"AQI 值 {aqi}:\n避免所有戶外活動，留在室內，關閉門窗，使用空氣淨化器，準備應急物品。")


    return "\n\n".join(advice)



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

@handler.add(MessageEvent, message=TextMessage)
def lunch_location_message(event):
    lineMessage = event.message.text
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



