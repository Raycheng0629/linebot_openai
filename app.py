from flask import Flask, request, abort
import os
import json
import requests
import googlemaps
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, URITemplateAction
import random

app = Flask(__name__)

# Initialize Google Maps API client
gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))

# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    lineMessage = event.message.text
    if lineMessage[0:3] == "隨便吃":
        lineMes = lineMessage
        if lineMes[4:].strip() == '':
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="查無餐廳"))
            return
        else:
            address = lineMes[4:].strip()
        
        addurl = 'https://maps.googleapis.com/maps/api/geocode/json?key={}&address={}&sensor=false'.format(os.getenv('GOOGLE_MAPS_API_KEY'), address)
        addressReq = requests.get(addurl)
        addressDoc = addressReq.json()
        
        if not addressDoc['results']:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="查無餐廳"))
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
        
        res_num = len(top20_restaurants)
        bravo = []
        
        for i in range(res_num):
            try:
                if top20_restaurants[i]['rating'] > 3.9:
                    bravo.append(i)
            except KeyError:
                continue
        
        if len(bravo) < 8:
            content = "沒找到高評分的店家，隨便選一家"
            restaurant = top20_restaurants[random.choice(range(res_num))]
        else:
            restaurant = top20_restaurants[random.choice(bravo)]
        
        if restaurant.get("photos") is None:
            thumbnail_image_url = None
        else:
            photo_reference = restaurant["photos"][0]["photo_reference"]
            photo_width = restaurant["photos"][0]["width"]
            thumbnail_image_url = "https://maps.googleapis.com/maps/api/place/photo?key={}&photoreference={}&maxwidth={}".format(os.getenv('GOOGLE_MAPS_API_KEY'), photo_reference, photo_width)
        
        rating = "無" if restaurant.get("rating") is None else restaurant["rating"]
        address = "沒有資料" if restaurant.get("vicinity") is None else restaurant["vicinity"]
        details = "Google Map分數: {}\n地址: {}".format(rating, address)
        
        map_url = "https://www.google.com/maps/search/?api=1&query={},{}&query_place_id={}".format(
            restaurant["geometry"]["location"]["lat"],
            restaurant["geometry"]["location"]["lng"],
            restaurant["place_id"]
        )
        
        buttons_template = TemplateSendMessage(
            alt_text=restaurant["name"],
            template=ButtonsTemplate(
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
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
