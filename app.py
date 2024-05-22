import os
import time
import json
import requests
import googlemaps
from flask import Flask, request, abort
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, LocationMessage, QuickReply, QuickReplyButton, MessageAction

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

exclude_keywords = [
    "即時", "要聞", "娛樂", "運動", "全球", "社會", "地方",
    "產經", "股市", "房市", "生活", "寵物", "健康", "橘世代",
    "文教", "評論", "兩岸", "科技", "Oops", "閱讀", "旅遊",
    "雜誌", "報時光", "倡議+", "500輯", "轉角國際", "NBA",
    "時尚", "汽車", "棒球", "HBL", "遊戲", "專題", "網誌",
    "女子漾", "倡議家"
]

def get_news(url):
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
                    absolute_link_url = urljoin(response.url, link_url)  # 轉換為絕對路徑
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

def get_extreme_weather_news():
    url = "https://udn.com/search/tagging/2/%E6%A5%B5%E7%AB%AF%E6%B0%A3%E5%80%99"
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
                    absolute_link_url = urljoin(response.url, link_url)  # 轉換為絕對路徑

                    # 過濾掉包含排除關鍵詞的標題
                    if not any(keyword in link_text for keyword in exclude_keywords):
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
    try:
        url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/{city_id}?Authorization={code}&sort=time'
        req = requests.get(url)
        data = req.json()
        location = data['records']['locations'][0]['location']
        for loc in location:
            if loc['locationName'] in address:
                weather = loc['weatherElement'][6]['time'][0]['elementValue'][0]['value']
                max = loc['weatherElement'][1]['time'][0]['elementValue'][0]['value']
                min = loc['weatherElement'][2]['time'][0]['elementValue'][0]['value']
                pop = loc['weatherElement'][0]['time'][0]['elementValue'][0]['value']
                if not f'{loc["locationName"]}' in result:
                    result[f'{loc["locationName"]}'] = f'{now} - {now2}天氣狀況「{weather}」，最高溫 {max} 度，最低溫 {min} 度，降雨機率 {pop}%！'
    except Exception as e:
        print(e)
    result = [value for key, value in result.items() if key in address]
    return '\n'.join(result) if result else '找不到氣象資訊'

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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text

    if text == "新聞":
        buttons = []
        for category in news_categories:
            buttons.append(QuickReplyButton(action=MessageAction(label=category, text=category)))
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請選擇新聞類型", quick_reply=QuickReply(items=buttons))
        )
    elif text in news_categories:
        news_list = get_news(news_categories[text])
        if news_list:
            messages = [TextSendMessage(text=f"{news['title']}\n{news['url']}") for news in news_list[:5]]
            line_bot_api.reply_message(event.reply_token, messages)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到新聞"))
    elif text.startswith("地震"):
        eq_data = earth_quake()
        if eq_data[1]:
            message = [TextSendMessage(text=eq_data[0]), ImageSendMessage(original_content_url=eq_data[1], preview_image_url=eq_data[1])]
        else:
            message = [TextSendMessage(text=eq_data[0])]
        line_bot_api.reply_message(event.reply_token, message)
    elif text.startswith("天氣"):
        location = text[2:].strip()
        weather_data = weather(location)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=weather_data))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請選擇新聞、地震或天氣資訊"))

if __name__ == "__main__":
    app.run()
