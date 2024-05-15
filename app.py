from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

app = Flask(__name__)

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
    if event.message.text == "即時新聞":
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')  # 選擇以無頭模式啟動Chrome，避免彈出視窗
            driver = webdriver.Chrome(options=options, executable_path="chromedriver.exe")
            
            driver.get("https://udn.com/news/breaknews/1")
            time.sleep(10)

            container_elements = driver.find_elements(By.CLASS_NAME, "story-list__text")
            news_links = []
            for container_element in container_elements:
                try:
                    link_elements = container_element.find_elements(By.TAG_NAME, "a")
                    for link_element in link_elements:
                        link_text = link_element.text
                        link_url = link_element.get_attribute("href")
                        news_links.append(f"{link_text}: {link_url}")
                except Exception as e:
                    print("連結提取失敗:", str(e))
            
            driver.quit()

            if news_links:
                reply_message = "\n".join(news_links[:5])  # 取前5個新聞連結
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="抱歉，目前沒有最新新聞。"))

        except Exception as e:
            print("爬取新聞失敗:", str(e))
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="抱歉，爬取新聞時出現了一些問題。"))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
