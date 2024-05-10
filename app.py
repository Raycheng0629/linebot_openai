import os
import json
from linebot import LineBotApi, WebhookHandler
import os
import json
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    TextSendMessage, StickerSendMessage, ImageSendMessage, VideoSendMessage,
    AudioSendMessage, LocationSendMessage, TemplateSendMessage, CarouselTemplate,
    CarouselColumn, ButtonsTemplate, PostbackAction, URIAction, MessageAction,
    ImageCarouselTemplate, ImageCarouselColumn, QuickReply, QuickReplyButton,
    ConfirmTemplate, CameraAction, CameraRollAction, LocationAction,
    DatetimePickerAction, FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent, ImageComponent, ImagemapSendMessage, BaseSize,
    URIImagemapAction, MessageImagemapAction, ImagemapArea
) # 看需要用到甚麼再import甚麼

token = os.getenv('CHANNEL_ACCESS_TOKEN'')
secret = os.getenv('CHANNEL_SECRET')

line_bot_api = LineBotApi(token)
handler = WebhookHandler(secret)

def handle_text_message(msg):
elif msg == '今日運勢':
        return TextSendMessage(
            text='選擇一個動作',
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=CameraAction(label='晴天'),
                        image_url='https://storage.googleapis.com/你的icon連結.png'
                    ),
                    QuickReplyButton(
                        action=CameraRollAction(label='雨天'),
                        image_url='https://storage.googleapis.com/你的icon連結.png'
                    ),
                    QuickReplyButton(
                        action=LocationAction(label='多雲'),
                        image_url='https://storage.googleapis.com/你的icon連結.png'
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label='陰天', data='action=buy&itemid=123'),
                        image_url='https://storage.googleapis.com/你的icon連結.png'
                    ),
                    QuickReplyButton(
                        action=MessageAction(label='晴時多雲', text='訊息內容'),
                        image_url='https://storage.googleapis.com/你的icon連結.png'
                    )
                ]
            )
        )

def linebot(request):
    body = request.get_data(as_text=True)
    json_data = json.loads(body)

    try:
        signature = request.headers['X-Line-Signature']
        handler.handle(body, signature)

        event = json_data['events'][0]
        tk = event['replyToken']
        msg_type = event['message']['type']

        if msg_type == 'text':
            msg = event['message']['text']
            reply_msg = handle_text_message(msg)
            line_bot_api.reply_message(tk, reply_msg)
        else:
            reply_msg = TextSendMessage(text='你傳的不是文字訊息呦')
            line_bot_api.reply_message(tk, reply_msg)

    except Exception as e:
        detail = e.args[0]
        print(detail)

    return 'OK'
