import asyncio
import os
import threading

from amiyabot import Message, Chain

from core import Requirement

from .src.plugin_instance import StableDiffusionPluginInstance
from .src.message_handler import get_channel_queue,handle_message

curr_dir = os.path.dirname(__file__)


bot : StableDiffusionPluginInstance = None

def dynamic_get_global_config_schema_data():
    if bot:
        return bot.generate_schema()
    else:
        return f'{curr_dir}/accessories/global_config_default.json'

bot = StableDiffusionPluginInstance(
    name='StableDiffusion绘图',
    version='0.2.2',
    plugin_id='amiyabot-hsyhhssyy-stable-diffusion',
    plugin_type='',
    description='安装前请读一下插件文档',
    document=f'{curr_dir}/README.md',
    global_config_default=f'{curr_dir}/accessories/global_config_default.json',
    global_config_schema = dynamic_get_global_config_schema_data
)

def enabled_in_this_channel(channel_id:str) -> bool:
    black_list_mode:bool = bot.get_config("black_list_mode")
    black_white_list:list = bot.get_config("black_white_list")


    if black_list_mode:
        if black_white_list is not None and channel_id in black_white_list:
            return False
        else:
            return True
    else:
        if black_white_list is not None and channel_id in black_white_list:
            return True
        else:
            return False

@bot.on_message(keywords=['兔兔查询绘图队列'],level=114514)
async def _(data: Message):

    if enabled_in_this_channel(data.channel_id) == False:
        return

    queue_text = get_channel_queue(data.channel_id)
    if len(queue_text) == 0:
        await data.send(Chain(data, at=False).text(f'当前频道没有正在处理的兔兔绘图任务。'))
        return
    
    queue_text_join = '\n'.join(queue_text)

    await data.send(Chain(data, at=False).text(f'当前频道正在处理的兔兔绘图任务：\n{queue_text_join}'))

@bot.on_message(keywords=['兔兔绘图'],level=114514)
async def _(data: Message):

    if enabled_in_this_channel(data.channel_id) == False:
        return

    if bot.webui_api is None:
        bot.debug_log(f"未加载WebUIApi，汇报错误。")
        no_service_prompt = bot.get_config("no_service_prompt")
        if no_service_prompt and no_service_prompt != "":
            await data.send(Chain(data, at=False).text(no_service_prompt))
        else:
            await data.send(Chain(data, at=False).text(f'抱歉，暂时无法提供服务。'))
        return
    
    await handle_message(bot,data)
