import os
import random
import re
import threading
import queue
import asyncio
import traceback

from amiyabot import Chain
from .plugin_instance import StableDiffusionPluginInstance
from .stable_diffusion import simple_img_task
from ..lib.command_line_utils import parse_command

curr_dir = os.path.dirname(__file__)

MAX_TASKS_PER_CHANNEL = 2
MAX_GLOBAL_TASKS = 5

HintFile = f"{curr_dir}/../accessories/Hints.txt"

current_task_count = 0

# 创建任务队列
task_queue = queue.Queue()
# 频道任务计数
channel_task_count = {}
# 队列锁
queue_lock = threading.Lock()

new_loop = asyncio.new_event_loop()

def get_channel_queue(channel_id):
    if queue_lock.acquire(timeout=5):  # 尝试获取锁，等待最多5秒
        try:
            # 使用列表解析式从队列中检索与特定频道相关的任务
            return [task['prompt'] for task in list(task_queue.queue) if task['data'].channel_id == channel_id]
        finally:
            queue_lock.release()  # 无论如何都确保释放锁
    else:
        # 超时后的处理，例如返回一个错误信息或空列表
        return []

def get_global_queue():
    if queue_lock.acquire(timeout=5):  # 尝试获取锁，等待最多5秒
        try:
            # 使用列表解析式从队列中检索所有任务的data.text
            return [task['prompt'] for task in list(task_queue.queue)]
        finally:
            queue_lock.release()  # 无论如何都确保释放锁
    else:
        # 超时后的处理，例如返回一个错误信息或空列表
        return []


def count_time(plugin,prompt):
    resolution = plugin.get_config("standard_resolution")
    if resolution is None or not re.match(r'^\d+:\d+$', resolution):
        resolution = "512:512"
    
    batch_count = plugin.get_config("batch_count")

    # 计算绘图时间，每512x512像素面积的图片需要50秒
    estimate_time = int(batch_count) * 50 * (int(resolution.split(':')[0]) * int(resolution.split(':')[1]) / (512 * 512))

    # 约到整10秒
    estimate_time = round(estimate_time / 10) * 10

    _, param_dict = parse_command(prompt.strip())

    if "hr" in param_dict.keys():
        estimate_time = estimate_time * 2
    
    if "lr" in param_dict.keys():
        estimate_time = estimate_time / 2

    return estimate_time

async def process_queue():

    global current_task_count

    asyncio.set_event_loop(new_loop)

    while True:
        task = task_queue.get()
        current_task_count = 1
        plugin, data, prompt,task = task['plugin'], task['data'], task['prompt'], task['task']
        if plugin is None:
            break
        
        plugin.debug_log(f"处理兔兔绘图任务循环")
        
        random_hint = None
        with open(HintFile, 'r', encoding='utf-8') as f:
            hints = [line for line in f.readlines() if not line.strip().startswith('#')]
            random_hint = hints[random.randint(0, len(hints)-1)]

        try:
            global_queue_length_str = ""
            if len(get_global_queue()) > 0:
                global_queue_length_str = f"(全局队列:{len(get_global_queue())})"
            
            is_img_to_img=""
            if data.image:
                is_img_to_img = "（图生图）"

            time = count_time(plugin,prompt)
            await data.send(Chain(data, at=False).text(f'兔兔开始绘制{is_img_to_img}，约需{round(time/2)}-{round(time)}秒，请稍等：{global_queue_length_str}\n{prompt}\n[小提示：{random_hint.strip()}]'))
            await simple_img_task(plugin, data, prompt,task)
        except Exception as e:
            stack_trace = traceback.format_exc()
            plugin.debug_log(f"兔兔绘图任务出现异常：{e}\n{stack_trace}")
        
        if queue_lock.acquire(timeout=5):  # 尝试获取锁，等待最多5秒
            try:
                channel_task_count[data.channel_id] -= 1
            finally:
                queue_lock.release()
        else:
            channel_task_count[data.channel_id] -= 1
        
        task_queue.task_done()
        
        current_task_count = 0
        
        # 异步休眠以减少CPU使用率
        await asyncio.sleep(1)

def run_event_loop():
    asyncio.set_event_loop(new_loop)
    asyncio.ensure_future(process_queue())
    new_loop.run_forever()

worker = threading.Thread(target=run_event_loop, daemon=True)
worker.start()

async def ChatGPTResponse(plugin: StableDiffusionPluginInstance, data):

    plugin.debug_log(f"进入兔兔绘图功能")

    prompt = None

    match = re.search(r'兔兔绘图[:：]\s?([\s\S]*)', data.text)
    if match:
        prompt = match.group(1)

    if not prompt:
        plugin.debug_log(f"正则表达式未通过")
        await data.send(Chain(data, at=False).text(f'抱歉，您提出的要求格式不正确。'))
        return

    if queue_lock.acquire(timeout=5):  # 尝试获取锁，等待最多5秒
        try:
            if task_queue.qsize() >= MAX_GLOBAL_TASKS:
                await data.send(Chain(data, at=False).text(f'抱歉，全局任务已满，请稍后再试。'))
                return

            channel_tasks = channel_task_count.get(data.channel_id, 0)
            if channel_tasks >= MAX_TASKS_PER_CHANNEL:
                await data.send(Chain(data, at=False).text(f'抱歉，当前频道任务队列已满，请稍后再试。'))
                return

            channel_task_count[data.channel_id] = channel_tasks + 1

            if current_task_count > 0 or task_queue.qsize() > 0:
                await data.send(Chain(data, at=False).text(f'兔兔当前有其他任务，您的任务已加入队列，请稍等......'))
            else:
                # await data.send(Chain(data, at=False).text(f'兔兔要开始画图了，请稍等......'))
                pass

            if data.image and len(data.image) > 0:
                task_queue.put({'plugin': plugin, 'data': data, 'prompt': prompt, 'task': "ImageToImage"})
            else:
                task_queue.put({'plugin': plugin, 'data': data, 'prompt': prompt, 'task': "TextToImage"})
        finally:
            queue_lock.release()  # 无论如何都确保释放锁
    else:
        # 超时后的处理，例如返回一个错误信息或空列表
        await data.send(Chain(data, at=False).text(f'抱歉，兔兔绘图任务队列锁获取超时，请稍后再试。'))
        
    return
