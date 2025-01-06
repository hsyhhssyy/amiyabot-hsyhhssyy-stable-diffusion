

import base64
import time
import requests

bce_creds = {
    "bce_token": None,
    "bce_expires_at": None
}

def get_token(bot):
    ak = bot.get_config("bce_ak")
    sk = bot.get_config("bce_sk")

    if not ak or not sk or ak == "" or sk == "":
        return None
    
    last_token_expires_at = bce_creds["bce_expires_at"]
    if last_token_expires_at and last_token_expires_at > int(time.time()):
        return bce_creds["bce_token"]

    bot.debug_log(f"正在获取bce token")

    url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={ak}&client_secret={sk}"
    
    payload = ""
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == 200:
        token = response.json().get("access_token")
        expires_in = response.json().get("expires_in") # unit is second
        bce_creds["bce_token"] = token
        bce_creds["bce_expires_at"] = int(time.time()) + expires_in - 3600 # 1 hours earlier
        bot.debug_log(f"获取bce token成功")
        return token    
    else:
        bot.debug_log(f"获取bce token失败: {response.text}")
        return None

# 返回False表示检测到Porn，None表示未配置。
def anti_porn(bot,image_bytes):
    token = get_token(bot)
    if not token:
        bot.debug_log(f"获取bce token失败")
        # 如果填写了AK SK 则返回false，否则返回None
        if ( bot.get_config("bce_ak") and bot.get_config("bce_ak") !="") or (bot.get_config("bce_sk") and bot.get_config("bce_sk") !=""):
            return False
        return None

    url = "https://aip.baidubce.com/rest/2.0/solution/v1/img_censor/v2/user_defined" + "?access_token=" + token
    
    # 将图片转换为base64
    img_base64 = base64.b64encode(image_bytes).decode('utf-8')

    params = {
        "image": img_base64
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    response = requests.request("POST", f"{url}", headers=headers, data=params)

    if response.status_code == 200:
        json =  response.json()
        if json["conclusion"] == "不合规":
            bot.debug_log(f'BCE认为结果不合规： {json}')
            return False
        else:
            return True
    else:
        bot.debug_log(f"请求百度AI失败: {response.text}")
        return False