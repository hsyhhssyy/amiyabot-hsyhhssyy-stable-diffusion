import asyncio
import os
import threading

from amiyabot import Message, Chain

from core import Requirement

from .src.plugin_instance import StableDiffusionPluginInstance
from .src.chatgpt_response import ChatGPTResponse,get_channel_queue,get_global_queue
from .lib.download_lora import download_from_civitai,word_replace_config

curr_dir = os.path.dirname(__file__)


bot : StableDiffusionPluginInstance = None

def dynamic_get_global_config_schema_data():
    if bot:
        return bot.generate_schema()
    else:
        return f'{curr_dir}/accessories/global_config_default.json'

bot = StableDiffusionPluginInstance(
    name='AI画图(StableDiffusion+ChatGPT)',
    version='0.2.1',
    plugin_id='amiyabot-hsyhhssyy-stable-diffusion',
    plugin_type='',
    description='（更新了插件商店不显示文档和预览的Bug）',
    document=f'{curr_dir}/README.md',
    requirements=[
        Requirement("amiyabot-blm-library")
    ],
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

@bot.on_message(keywords=['兔兔下载Lora'],level=114514,allow_direct=True,direct_only=True)
async def _(data: Message):
    if not data.is_admin:
        await data.send(Chain(data, at=False).text(f'抱歉，您没有权限。'))
        return
    
    # 创建一个Event用于等待线程完成
    done_event = asyncio.Event()
    
    def thread_func():
        try:
            download_from_civitai(10,bot)
        finally:
            # 线程完成时，设置事件
            done_event.set()

    thread = threading.Thread(target=thread_func)
    thread.start()

    await data.send(Chain(data, at=False).text(f'已开始下载Lora模型。'))
    
    # This function will send updates every minute
    async def send_progress_updates():
        while not done_event.is_set():
            await asyncio.sleep(60)  # Sleep for 1 minute
            await data.send(Chain(data, at=False).text(f'Lora模型下载进度：已下载{len(word_replace_config)}个模型。'))

    # Create a task for sending updates
    update_task = asyncio.create_task(send_progress_updates())

    # Wait for the thread to complete
    await done_event.wait()
    update_task.cancel()  # Cancel the update task when done

    await data.send(Chain(data, at=False).text(f'Lora模型下载完成，共下载{len(word_replace_config)}个模型。'))

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

    # 如果没有ChatGPT就走最简流程然后返回
    if bot.blm_plugin is None:
        bot.debug_log(f"未加载BLM插件，无法使用")
        return
    
    await ChatGPTResponse(bot,data)
