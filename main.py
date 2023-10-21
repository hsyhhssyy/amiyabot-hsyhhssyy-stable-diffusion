import asyncio
import os
import threading

from amiyabot import Message, Chain
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
    name='StableDiffusion+ChatGPT',
    version='0.0.1',
    plugin_id='amiyabot-hsyhhssyy-stable-diffusion',
    plugin_type='',
    description='StableDiffusion本地调用插件',
    document=f'{curr_dir}/README.md',
    global_config_default=f'{curr_dir}/accessories/global_config_default.json',
    global_config_schema = dynamic_get_global_config_schema_data
)


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

# @bot.on_message(keywords=['兔兔清除词语替换'],level=114514,allow_direct=True,direct_only=True)
# async def _(data: Message):
#     if not data.is_admin:
#         await data.send(Chain(data, at=False).text(f'抱歉，您没有权限。'))
#         return
    
#     bot.set_config("word-replace",[])
#     await data.send(Chain(data, at=False).text(f'已清除词语替换。'))


# @bot.on_message(keywords=['兔兔备份词语替换'],level=114514,allow_direct=True,direct_only=True)
# async def _(data: Message):
#     if not data.is_admin:
#         await data.send(Chain(data, at=False).text(f'抱歉，您没有权限。'))
#         return
    
#     bot.set_config("word-replace-backup",bot.get_config("word-replace"))
#     await data.send(Chain(data, at=False).text(f'已备份词语替换。'))

# @bot.on_message(keywords=['兔兔恢复备份词语替换'],level=114514,allow_direct=True,direct_only=True)
# async def _(data: Message):
#     if not data.is_admin:
#         await data.send(Chain(data, at=False).text(f'抱歉，您没有权限。'))
#         return
    
#     if len(bot.get_config("word-replace-backup")) == 0:
#         await data.send(Chain(data, at=False).text(f'没有备份词语替换。'))
#         return
#     bot.set_config("word-replace",bot.get_config("word-replace-backup"))
#     await data.send(Chain(data, at=False).text(f'已恢复备份词语替换。'))

@bot.on_message(keywords=['兔兔查询绘图队列'],level=114514)
async def _(data: Message):
    queue_text = get_channel_queue(data.channel_id)
    if len(queue_text) == 0:
        await data.send(Chain(data, at=False).text(f'当前频道没有正在处理的兔兔绘图任务。'))
        return
    
    queue_text_join = '\n'.join(queue_text)

    await data.send(Chain(data, at=False).text(f'当前频道正在处理的兔兔绘图任务：\n{queue_text_join}'))

@bot.on_message(keywords=['兔兔绘图'],level=114514)
async def _(data: Message):

    if bot.webui_api is None:
        bot.debug_log(f"未加载WebUIApi，汇报错误。")
        no_service_prompt = bot.get_config("no_service_prompt")
        if no_service_prompt and no_service_prompt != "":
            await data.send(Chain(data, at=False).text(no_service_prompt))
        else:
            await data.send(Chain(data, at=False).text(f'抱歉，暂时无法提供服务。'))
        return

    # 如果没有ChatGPT就走最简流程然后返回
    if bot.chatgpt_plugin is None:
        bot.debug_log(f"未加载ChatGPT插件，最简流程")
        return
    
    await ChatGPTResponse(bot,data)
