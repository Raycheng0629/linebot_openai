#5/15版本
from flask import Flask, request, abort
import math, json, time, requests
import os
import googlemaps
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, StickerSendMessage, ImageSendMessage, LocationMessage
import random

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
            '☀️ 陽光明媚，心情愉悅，今天適合外出活動，盡情享受陽光的溫暖。🌳🚴‍♂️去運動、旅行或與好友聚會，你會充滿活力和快樂。',
            '🌞 鳥語花香，樂觀向上，勇敢追尋夢想，今天會是你收獲的一天。📚📝積極投入工作或學習，你將收穫豐富的成果。',
            '☀️ 陽光灑落，希望無限，心想事成，把握機會，一切皆有可能。💡💬勇敢表達自己的想法和願望，你會被周圍的人支持與鼓勵。',
            '☀️ 晴空萬里，心情明朗，與朋友共度愉快時光，今天是個充滿笑聲的日子。🍽️🥂與家人或朋友共同享受美食和美好時光，你的心情會更加愉快。',
            '🌈 陽光燦爛，能量飽滿，充滿自信，挑戰自我，你會發現更強大的自己。💪🎉挑戰自己的極限，突破困難，你將收穫成長和成功的喜悅。'
        ],
        '晴時多雲': [
            '⛅ 陽光穿透雲層，希望即將到來，保持耐心，新的機遇即將出現。🌟💭專注於自己的目標和夢想，你會發現機會在不知不覺中出現。',
            '🌤 陽光間歇，心情變幻，但積極面對挑戰，你會發現事情並沒有那麼難。🔍💼相信自己的能力，堅持努力，你將克服困難，走向成功。',
            '⛅ 陽光與雲朵交替，讓人充滿期待，新的一天充滿了驚喜和希望。🌈💫保持開放的心態，接受生活的變化，你會發現美好就在不遠處。',
            '🌤 陽光時隱時現，把握當下，好好珍惜眼前的一切，幸福就在不遠處。💖🌼感恩生活中的每一個美好時刻，你會發現生活因此更加豐富多彩。',
            '⛅ 晴時多雲，讓人心情輕鬆，保持開放的心態，你會發現美好處處可見。👀🌺與家人或朋友一起享受悠閒的時光，你的心情將更加愉悅。'
        ],
        '雨天': [
            '🌧 細雨綿綿，心情輕柔，靜心聆聽雨聲，內心將會得到淨化和安寧。🎵📖找一個安靜的角落，沉澱心靈，你會找到內心的寧靜與安寧。',
            '🌧 雨聲綿綿，如詩如畫，靜心沉澱，你會找到內心的平靜與安寧。✍️🌱寫下你的想法和感受，讓情緒得到釋放，你會感到心情愈加舒暢。',
            '🌧 雨水滋潤大地，給予生命新的希望，讓心靈得到滋養，明天將會更加美好。🌈🌱感受雨水的滋潤和洗禮，你會找到生活的新動力和希望。',
            '🌦 雨中漫步，心情舒暢，讓雨水洗去塵世的疲憊，重新找回自我。🌿🌧享受雨水帶來的清新和愉悅，你會發現生活因此更加美好。',
            '🌧 雨中涼意，思緒清新，把握當下，尋找屬於你的幸福與溫暖。🌂💕與親友共度美好時光，分享彼此的感受和心情，你的心情會更加溫暖和愉悅。'
        ],
        '陰天': [
            '☁️ 陰天總讓人感到平靜，是理想的反思時刻，好好聆聽內心的聲音，你會找到答案。🧘‍♂️📝找到一個安靜的角落，思考人生的意義和方向，你會有所領悟。',
            '☁️ 陰雲籠罩，心情平和，適合靜心思考，你會發現一片新的天地。📚🌌閱讀一本好書或聆聽輕音樂，你會找到內心的平靜和安寧。',
            '☁️ 陰天帶來思考，挑戰也是成長的機會，勇敢面對，你會變得更加堅強。🔍💪接受生活的挑戰，勇敢面對困難，你會收穫成長和成功的喜悅。',
            '☁️ 陰天雖然暗淡，但別忘了陽光總會再度閃耀，相信明天會更好。🌅💭保持樂觀的態度，相信自己和未來，你會發現光明在不遠處。',
            '☁️ 陰天讓人感到安靜，適合尋找內心的平靜，好好放鬆，你會發現心靈的寧靜。🧘‍♀️🌳做些瑜伽或冥想，讓身心得到放鬆和平靜，你的心情會更加愉悅。'
        ],
        '多雲': [
            '🌥 天空多雲，讓人心情愉悅，充滿了神秘與期待，新的驚喜即將到來。🌈🔮保持好奇心，探索生活的無限可能性，你會發現驚喜處處可見。',
            '🌥 一朵朵白雲飄過，象徵著無限可能，今天是探索新事物的好日子。🚀🌌嘗試新的事物和挑戰，你會豐富自己的生活，收穫新的經驗和感受。',
            '🌥 多雲天氣，讓人心情變幻莫測，但這種變化也是生活的一部分，保持開放的態度，你會發現美好就在不遠處。🎨🌟接受生活的變化，享受當下的美好，你會更加快樂和滿足。',
            '🌥 天空多雲，把握當下，享受當下的美好，不要讓擔憂與煩惱擾亂你的心情。💖🌟感恩每一個美好的瞬間，你會發現生活因此更加豐富多彩。',
            '🌥 多雲的天空，讓人感到神秘與奇妙，保持好奇心，你會發現生活處處充滿驚喜。🔍🎉和家人或朋友一起探索大自然，你會收穫美好的回憶和情感。'
        ]
    }

    return random.choice(fortunes[weather])  # 從指定天氣的運勢結果中隨機選擇一個


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
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='請輸入你那邊的天氣狀況（晴天、陰天、晴時多雲、雨天、多雲等）'))
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
