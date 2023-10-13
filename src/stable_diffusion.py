import datetime
import json
import math
import os
import random
import re
from typing import List

from PIL import Image
from io import BytesIO

from amiyabot.network.download import download_sync
from amiyabot import Message, Chain

from core.resource.arknightsGameData import ArknightsGameData

from .plugin_instance import StableDiffusionPluginInstance,ALWAYS_ON_SCRIPTS_PATH

from ..lib.command_line_utils import parse_command
from ..lib.mathmatic import compute_dimensions
from ..lib.pil_utils import combine_images
from ..lib.download_lora import WORD_REPLACE_CONFIG_PATH

from ..src.chatgpt_presets import identify_character, generate_danbooru_tags

curr_dir = os.path.dirname(__file__)

OUTPUT_SAVE_PATH = f"{curr_dir}/../../../resource/stable-diffusion/output"

if not os.path.exists(OUTPUT_SAVE_PATH):
    os.makedirs(OUTPUT_SAVE_PATH)

async def word_replace(plugin,original_prompt:str):
    
    replace_source = plugin.get_config("word_replace")
    
    with open(WORD_REPLACE_CONFIG_PATH, 'r') as file:
        word_replace_config = json.load(file)
    
    if word_replace_config:
        replace_source += word_replace_config
    
    candidates = []

    for item in replace_source:
        splited_item_name = item["name"].split(",")

        for name in splited_item_name:
            name = name.strip()

            if name in original_prompt:
                candidates.append(item)
                break
    
    # 通过字符串匹配,找到预筛的干员列表
    not_operator_candidate = [candidate for candidate in candidates if not candidate.get("operator")]

    # 对于来自WORD_REPLACE_CONFIG_PATH的干员,需要通过ChatGPT识别角色
    operator_candidate = [candidate for candidate in candidates if candidate.get("operator")]
    
    candidates_for_chatgpt = {}

    id_to_operator = {op.id: op for op in ArknightsGameData.operators.values()}

    for operator in operator_candidate:
        op_id = operator["operator"]
        op = id_to_operator.get(op_id, None) 

        if not op:
            plugin.debug_log(f"找不到干员: {op_id}")
            continue

        # 根据 op.sex是男还是女,为op.name添加后缀先生或者小姐
        if op.sex == "男":  # Assuming the value for male is '男'
            op_name_with_suffix = op.name + "先生"
        elif op.sex == "女":  # Assuming the value for female is '女'
            op_name_with_suffix = op.name + "小姐"
        else:
            op_name_with_suffix = op.name + "干员"


        candidates_for_chatgpt[op_name_with_suffix]=operator

    char_json = await identify_character(plugin, candidates_for_chatgpt.keys(), original_prompt)

    if not char_json or char_json == {}:
        plugin.debug_log(f"未匹配到任何干员")
        return not_operator_candidate + []
    
    operator_candidate_final = [candidates_for_chatgpt[char_name] for char_name in char_json]

    plugin.debug_log(f"匹配到干员: {char_json} , {operator_candidate_final}")

    return not_operator_candidate + operator_candidate_final

def select_model(plugin,model_name):
    model_selector = plugin.get_config("model_selector")
    selected_models=[]
    if model_selector:
        for model in model_selector:
            if model["style"].lower() == model_name.lower():
                selected_models.append(model)
    
    if len(selected_models) == 0:
        default_model = plugin.get_config("default_model")
        if default_model:
            return default_model
        return None

    # 随机选择一个
    return random.choice(selected_models)


async def simple_img_task(plugin: StableDiffusionPluginInstance, data: Message, user_prompt: str, task: str):

    plugin.debug_log(f"绘图 完整流程")

    user_prompt, param_dict = parse_command(user_prompt.strip())

    ar_param = param_dict.get('ar')

    width, height = compute_dimensions(ar_param,plugin.get_config("standard_resolution"))

    if param_dict.get('hr') == True:
        # 修改长宽，使得保持纵横比的情况下总像素面积提升一倍
        scale_factor = math.sqrt(2)
        width = int(width * scale_factor)
        height = int(height * scale_factor)
    
    if param_dict.get('lr') == True:
        # 修改长宽，使得保持纵横比的情况下总像素面积缩小一半
        scale_factor = math.sqrt(0.5)
        width = int(width * scale_factor)
        height = int(height * scale_factor)

    images_in_prompt = None
    if data.image:
        for imgPath in data.image:
            imgBytes = download_sync(imgPath)
            pilImage = Image.open(BytesIO(imgBytes))
            images_in_prompt.append(pilImage)

    # 对提示词搜索角色

    character_candidate = await word_replace(plugin, user_prompt)

    danbooru_tags = await generate_danbooru_tags(plugin, user_prompt)

    # 读取

    if len(danbooru_tags) > 0:
        drawing_params = []

        for answer_item in danbooru_tags:

            # 处理提示词
            sd_prompt = answer_item["prompt"]
            for char_setting in character_candidate:
                sd_prompt = sd_prompt + "," + char_setting["value"]

            options = {}

            sd_model = select_model(plugin, answer_item["style"])
            if sd_model is not None and sd_model["model"] != "...":
                options['sd_model_checkpoint'] = sd_model["model"]

            sampler_index = "Euler a"
            if sd_model is not None and sd_model["sampler"] != "...":
                sampler_index = sd_model["sampler"]

            if sd_model is not None and sd_model["prompts"] != "...":
                sd_prompt = sd_prompt + "," + sd_model["prompts"]
            
            if sd_model is not None and sd_model["vae"] != "..." and sd_model["vae"] != "":
                options['sd_vae'] = sd_model["vae"]

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
                "images": images_in_prompt,
                "task":task,
                # below are params for webui_api.set_options
                "options": options,
                # below are params for webui_api.txt2img
                "prompt": sd_prompt,
                "negative_prompt": negative_prompt,
                "seed": seed,
                "styles": [],
                "steps": 20,
                "cfg_scale": 7,
                "sampler_index": sampler_index,
                "width": width,
                "height": height,
                "alwayson_scripts": json.load(open(ALWAYS_ON_SCRIPTS_PATH, 'r', encoding='utf-8'))
            }

            drawing_params.append(drawing_param)

        use_grid = plugin.get_config("output_grid_first")

        plugin.debug_log(f"启用Grid")

        grid_start_time = datetime.datetime.now()

        images_output = []

        drawing_params = sorted(
            drawing_params, key=lambda x: x["options"]["sd_model_checkpoint"])

        answer_item_count = 0

        for drawing_param in drawing_params:
            
            plugin.debug_log(f"当前任务: {drawing_param['task']}")
            plugin.debug_log(f"使用模型: {drawing_param['sd_model']} VAE:{drawing_param['sd_model'].get('vae')}")
            plugin.debug_log(f"准备绘制: {drawing_param['prompt']}")
            plugin.debug_log(f"负面提示: {drawing_param['negative_prompt']}")

            answer_item_count += 1
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
                "height",
                "alwayson_scripts"]}
            if task == "TextToImage":
                selected_params = {**selected_params,
                                   **{
                                       
                                   }}
                result = plugin.webui_api.txt2img(**selected_params)
            else:
                result = plugin.webui_api.img2img(
                    images=[drawing_param["images"][0]], **selected_params)

            images_output.append(result.image)

            total_second = round(
                (datetime.datetime.now() - start_time).total_seconds(), 2)

            plugin.debug_log(f"绘制完成: {result.info}")
            if plugin.get_config("save_result"):
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                result.image.save(
                    f'{OUTPUT_SAVE_PATH}/StableDiffusionPlugin.v{plugin.version}.{timestamp}.png')

            if not use_grid:
                buffer = BytesIO()
                result.image.save(buffer, format="PNG")
                img_bytes = buffer.getvalue()
                await data.send(Chain(data, at=False).text(f'绘图结果({answer_item_count}/{len(drawing_params)})，用时{total_second}秒:').image(img_bytes))

        grid_total_second = round(
            (datetime.datetime.now() - grid_start_time).total_seconds(), 2)

        if len(images_output) > 1 and use_grid:
            new_img = combine_images(images_output)
            buffer = BytesIO()
            new_img.save(buffer, format="PNG")
            img_bytes = buffer.getvalue()
            await data.send(Chain(data, at=False).text(f'绘图结果，用时{grid_total_second}秒：').image(img_bytes))
    else:
        plugin.debug_log(f"ChatGPT Response not success")
        await data.send(Chain(data, at=False).text(f'真抱歉，兔兔画图失败了，请再试一次吧。'))

    plugin.debug_log(f"退出兔兔绘图功能")
