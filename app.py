from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
import os
import requests
from bs4 import BeautifulSoup

# Initialize Flask app
app = Flask(__name__)

# Initialize Line Bot API
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# OPENAI API Key initialization
openai.api_key = os.getenv('OPENAI_API_KEY')

# Temporary directory for storing files
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

# Function to get GPT response
def GPT_response(text):
    response = openai.Completion.create(model="gpt-3.5-turbo-instruct", prompt=text, temperature=0.5, max_tokens=500)
    answer = response['choices'][0]['text'].replace('。','')
    return answer

# Function for scraping PTT Movie board
def scrape_ptt_movie():
    url = "https://www.ptt.cc/bbs/movie/index.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.find_all("div", class_="r-ent")
    for a in articles:
        title = a.find("div", class_="title")
        if title and title.a:
            title = title.a.text
        else:
            title = "沒有標題"

        popular = a.find("div", class_="nrec")
        if popular and popular.span:
            popular = popular.span.text
        else:
            popular = "N/A"

        date = a.find("div", class_="date")
        if date:
            date = date.text
        else:
            date = "無顯示日期"
        yield f"標題:{title},人氣:{popular},日期:{date}"

# Callback route for Line webhook
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

# Message handling function
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    try:
        GPT_answer = GPT_response(msg)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage('OPENAI API key額度可能已經超過'))

# Postback event handling
@handler.add(PostbackEvent)
def handle_postback(event):
    print(event.postback.data)

# Member joined event handling
@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)

# Route for scraping PTT Movie board
@app.route("/scrape_ptt_movie")
def scrape_ptt_movie_route():
    data = scrape_ptt_movie()
    return "<br>".join(data)

# Main
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
