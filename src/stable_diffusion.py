import datetime
import os
import random
import re
from typing import List

from PIL import Image
from io import BytesIO

from amiyabot.network.download import download_sync
from amiyabot import Message,log, Chain
from ..lib.extract_json import ask_chatgpt_with_json
from .plugin_instance import StableDiffusionPluginInstance
from ..lib.webuiapi import HiResUpscaler

curr_dir = os.path.dirname(__file__)

OUTPUT_SAVE_PATH = f"{curr_dir}/../../../resource/stable-diffusion/output"

if not os.path.exists(OUTPUT_SAVE_PATH):
            os.makedirs(OUTPUT_SAVE_PATH)

def is_chinese(char: str) -> bool:
    """
    判断一个字符是否为中文
    """
    return '\u4e00' <= char <= '\u9fff'

def is_any_chinese(texts: List[str]) -> bool:
    """
    判断一个字符串列表中是否有包含中文的字符串
    """
    for text in texts:
        for char in text:
            if is_chinese(char):
                return True
    return False

def parse_command(s):
    # 提取基本命令，先去掉可能的 -ar 和 -hr 参数
    base_command = re.sub(r' -ar \d+:\d+', '', s)
    base_command = re.sub(r' -hr', '', base_command).strip()

    # 提取-ar参数
    ar_match = re.search(r'-ar (\d+:\d+)', s)
    ar_param = ar_match.group(1) if ar_match else None

    # 检查-hr参数是否存在
    hr_param = '-hr' in s

    return base_command, ar_param, hr_param

def compute_dimensions(ar):

    if ar is None:
        return 512,512

    # 将长宽比分解为a和b
    a, b = map(int, ar.split(':'))
    
    # 计算w
    w = (262144 / (a * b))**0.5
    
    # 计算宽度和高度
    width = int(a * w)
    height = int(b * w)
    
    return width, height

def combine_images(images):
    if not images:
        raise ValueError("The images list is empty!")

    width, height = images[0].size

    # 根据给定的图像数量决定输出图像的大小
    if len(images) == 1:
        new_img = Image.new('RGB', (width, height))
        positions = [(0, 0)]
    elif len(images) == 2:
        new_img = Image.new('RGB', (2 * width, height))
        positions = [(0, 0), (width, 0)]
    elif len(images) == 3:
        new_img = Image.new('RGB', (2 * width, 2 * height))
        positions = [(0, 0), (width, 0), (0, height)]
    elif len(images) == 4:
        new_img = Image.new('RGB', (2 * width, 2 * height))
        positions = [(0, 0), (width, 0), (0, height), (width, height)]
    else:
        raise ValueError("The images list should contain between 1 and 4 images.")

    # 将图像粘贴到新的空白图像上
    for img, position in zip(images, positions):
        new_img.paste(img, position)

    return new_img

async def simple_img_task(plugin:StableDiffusionPluginInstance, data:Message, user_prompt:str, task:str):
    
    plugin.debug_log(f"Txt2Img 完整流程")

    user_prompt, ar_param, hr_param = parse_command(user_prompt.strip())

    plugin.debug_log(f"ar_param: {ar_param} hr_param: {hr_param} prompt: {user_prompt}")

    width, height = compute_dimensions(ar_param)

    command = "<<PROMPT>>"

    with open(f'{curr_dir}/../templates/sd-template-v3.txt', 'r', encoding='utf-8') as file:
        command = file.read()
    
    command = command.replace("<<PROMPT>>", user_prompt)
    
    retry = 0
    
    images_in_prompt = []

    if data.image:
        for imgPath in data.image:
            imgBytes = download_sync(imgPath)
            pilImage = Image.open(BytesIO(imgBytes))
            images_in_prompt.append(pilImage)

    while retry < 3:
        retry += 1
        success,answer = await ask_chatgpt_with_json(plugin.chatgpt_plugin, prompt=command ,model='gpt-3.5-turbo')

        check_passed = True

        if success and len(answer) > 0:
            for answer_item in answer[0]:
                subjects = answer_item["subjects"]
                # subject里没中文不算成功
                # 但是三次都没有中文就算成功,因为可能是英文prompt
                if not is_any_chinese(subjects):
                    plugin.debug_log(f"Subject不包含中文: {subjects}")
                    check_passed = False
                    break
        else:
            check_passed = False
        
        if check_passed:
            break
             
    if success and len(answer) > 0:
        drawing_params = []

        for answer_item in answer[0]:
            
            sd_prompt = answer_item["prompt"]
            
            sd_prompt , append_str = plugin.word_replace(answer_item,user_prompt)

            sd_model = plugin.select_model(answer_item["style"])

            options = {}

            if sd_model is not None and sd_model["model"] != "...":
                options['sd_model_checkpoint'] = sd_model["model"] 

            sampler_index = "Euler a"
            if sd_model is not None and sd_model["sampler"] != "...":
                sampler_index = sd_model["sampler"] 

            if sd_model is not None and sd_model["prompts"] != "...":
                sd_prompt = sd_prompt + "," + sd_model["prompts"]

            sd_prompt = sd_prompt + ", " + append_str
            
            positive_prompts = plugin.get_config("positive_prompts")

            sd_prompt = sd_prompt + ", " + positive_prompts

            negative_prompt = plugin.get_config("negative_prompts")

            seed = random.randint(0, 2147483647)

            # # fixed param for testing
            # seed = 114514
            # negative_prompt = ""
            # final_prompt = "1girl"

            drawing_param = {
                # below are params for my logic
                "sd_model": sd_model,
                "images":images_in_prompt,
                # below are params for webui_api.set_options
                "options": options,
                # below are params for webui_api.txt2img
                "prompt": sd_prompt,
                "negative_prompt": negative_prompt,
                "seed": seed,
                "styles": [],
                "steps":20,
                "cfg_scale": 7,
                "sampler_index": sampler_index,
                "enable_hr": hr_param,
                "hr_scale": 2,
                "hr_upscaler": HiResUpscaler.Latent,
                "width": width,
                "height": height
            }

            
            plugin.debug_log(f"当前任务: {task}")
            plugin.debug_log(f"使用模型: {drawing_param['sd_model']}")
            plugin.debug_log(f"准备绘制: {drawing_param['prompt']}")
            plugin.debug_log(f"负面提示: {drawing_param['negative_prompt']}")

            drawing_params.append(drawing_param)

            # # break for testing
            # break

        use_grid = plugin.get_config("output_grid_first")

        
        plugin.debug_log(f"启用Grid")

        grid_start_time = datetime.datetime.now()

        images_output = []
        
        drawing_params = sorted(drawing_params, key=lambda x: x["options"]["sd_model_checkpoint"])

        answer_item_count = 0

        for drawing_param in drawing_params:
            
            answer_item_count+=1
            start_time = datetime.datetime.now()

            plugin.webui_api.set_options(drawing_param["options"])
            selected_params = {k: drawing_param[k] for k in [
                "prompt", 
                "negative_prompt", 
                "seed", 
                "styles",
                "steps", 
                "cfg_scale", 
                "sampler_index",
                "width",
                "height"]}
            if task == "TextToImage":
                result = plugin.webui_api.txt2img(**selected_params)
            else:
                result = plugin.webui_api.img2img(images=[drawing_param["images"][0]],**selected_params)

            images_output.append(result.image)

            total_second = round((datetime.datetime.now() - start_time).total_seconds(), 2)

            plugin.debug_log(f"绘制完成: {result.info}")
            if plugin.get_config("save_result"):
                timestamp =  datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                result.image.save(f'{OUTPUT_SAVE_PATH}/StableDiffusionPlugin.v{plugin.version}.{timestamp}.png')

            if not use_grid:
                buffer = BytesIO()
                result.image.save(buffer, format="PNG")
                img_bytes = buffer.getvalue()
                await data.send(Chain(data, at=False).text(f'绘图结果({answer_item_count}/{len(answer[0])})，用时{total_second}秒:').image(img_bytes))
        
        grid_total_second = round((datetime.datetime.now() - grid_start_time).total_seconds(),2)

        if len(images_output) > 1 and use_grid:
            new_img = combine_images(images_output)
            buffer = BytesIO()
            new_img.save(buffer, format="PNG")
            img_bytes = buffer.getvalue()
            await data.send(Chain(data, at=False).text(f'绘图结果，用时{grid_total_second}秒：').image(img_bytes))
    else:
        plugin.debug_log(f"ChatGPT Response not success: {answer}")
        await data.send(Chain(data, at=False).text(f'真抱歉，兔兔画图失败了，请再试一次吧。'))
   

    plugin.debug_log(f"退出兔兔绘图功能")