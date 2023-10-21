import json

from amiyabot.adapters.mirai.builder import MiraiMessageCallback
from amiyabot.adapters.cqhttp import CQHttpBotInstance

def get_quote_id(data):
    message = data.message
    if type(data.instance) == CQHttpBotInstance and 'message' in message.keys():
        if len(message['message']) >= 2:
            # print(f'{message}')
            if message['message'][0]['type'] == 'reply' and message['message'][1]['type'] == 'at':
                if f"{message['message'][1]['data']['qq']}" == f'{data.instance.appid}':
                    # print(f"is quote {message['message'][0]['data']['id']}")
                    return message['message'][0]['data']['id']
    elif 'messageChain' in message.keys():
        for msg in message['messageChain']:
            if msg['type']=='Quote':
                sender = msg['senderId']
                if f'{sender}' == f'{data.instance.appid}':
                    # print(f"is quote {msg['id']}")
                    return msg['id']
    return 0

def get_response_id(callback):
    if isinstance(callback, MiraiMessageCallback):
        response_dict = json.loads(callback.response)
        id = response_dict['messageId']
        return id
    return None