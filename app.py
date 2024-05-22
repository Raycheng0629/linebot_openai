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
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, LocationMessage, QuickReply, QuickReplyButton, MessageAction, ImageCarouselTemplate, ImageCarouselColumn, TemplateSendMessage, URIAction

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

def get_extreme_weather_news():
    exclude_keywords = []  # 添加這行
    response = requests.get("https://udn.com/search/tagging/2/%E6%A5%B5%E7%AB%AF%E6%B0%A3%E5%80%99")
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
                result[f'{city}{area}'] += '\n\n'
            result[f'{city}{area}'] += f'未來三小時 {note}'
        except Exception as e:
            print(e)
            result[f'{city}{area}'] = '未來三小時天氣資訊取得失敗'
    return '\n\n'.join([f'{k}:\n{v}' for k, v in result.items() if k in address])

@app.route("/", methods=['GET'])
def hello():
    return "Hello World!"

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
                if text == '氣象新聞':
                    news_data = get_extreme_weather_news()
                else:
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

if __name__ == "__main__":
    app.run()
