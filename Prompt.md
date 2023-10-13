import os
import re

from amiyabot import Chain
from .plugin_instance import StableDiffusionPluginInstance
from .stable_diffusion import txt_to_img

curr_dir = os.path.dirname(__file__)

async def ChatGPTResponse(plugin:StableDiffusionPluginInstance ,data):

    plugin.debug_log(f"进入兔兔绘图功能")

    await data.send(Chain(data, at=False).text(f'兔兔要开始画图了，请稍等......'))
    
    prompt = None

    match = re.search(r'兔兔绘图[:：]\s?([\s\S]*)', data.text)
    if match:
        prompt = match.group(1)
    
    if not prompt:
        plugin.debug_log(f"正则表达式未通过")
        await data.send(Chain(data, at=False).text(f'抱歉，您提出的要求格式不正确。'))
        return
    
    await txt_to_img(plugin, data, prompt)
    

    return

上面是我的一个python的代码,用来在qq消息bot中提供绘图功能
他有一个严重的问题就是,txt_to_img函数不可以多线程调用.但是ChatGPTResponse是可能会因为多个群聊中的多个人发出指令而被多线程触发的.

因此我需要做一个改动,提供队列能力(频道id可以从data.channel_id获取.)

每个频道有人发送指令时,自动进入队列.每个频道最多允许排队10个任务.频道队列已满时提示并禁止入队
全局超过30个任务时,提示并禁止入队

而text_to_img使用一个另外启动的线程,遍历全局队列并进行绘图任务,

mklink /D "C:\StableDiffusion\Aki\sd-webui-aki-v4.2\embeddings\Arknights-Auto" "\\192.168.31.25\mnt\raid1-pool1\amiya-bot\2912336120\resource\stable-diffusion\embeddings"