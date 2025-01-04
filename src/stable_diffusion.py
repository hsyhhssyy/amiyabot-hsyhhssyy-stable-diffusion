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

from .plugin_instance import StableDiffusionPluginInstance

from ..lib.webuiapi import ControlNetUnit
from ..lib.command_line_utils import parse_command
from ..lib.mathmatic import compute_dimensions, compute_dimensions_from_value
from ..lib.pil_utils import combine_images
from ..lib.bot_core_util import get_response_id
from ..lib.string_utils import extract_outer_parentheses

from core import bot as main_bot

curr_dir = os.path.dirname(__file__)

OUTPUT_SAVE_PATH = f"{curr_dir}/../../../resource/stable-diffusion/output"

if not os.path.exists(OUTPUT_SAVE_PATH):
    os.makedirs(OUTPUT_SAVE_PATH)

genrated_images = {}


async def generate_danbooru_tags(plugin, user_prompt: str) -> str:

    blm_model_name = plugin.get_config("ai_translate")

    if blm_model_name is None or blm_model_name == "..." or blm_model_name == "":
        return user_prompt

    if 'amiyabot-blm-library' not in main_bot.plugins.keys():
        return user_prompt

    blm_lib = main_bot.plugins['amiyabot-blm-library']

    if blm_lib is None:
        return user_prompt

    # # 对用户输入的prompt进行预处理，切分出所有以小括号包围的部分，保存下来，不传递给AI而是直接拼接在结果后面(逗号分隔)
    # tags_in_prompt, processed_prompt = extract_outer_parentheses(user_prompt)

    # if processed_prompt == "":
    #     return user_prompt

    # if len(tags_in_prompt) > 0:
    #     tags_in_prompt = "," + ",".join(tags_in_prompt)
    # else:
    #     tags_in_prompt = ""

    # 对用户输入的prompt进行预处理，以英文和中文逗号切分，如果切分出的内容不包含中文，则拼接到tags_in_prompt，否则拼接到processed_prompt
    tags_in_prompt = ""
    processed_prompt = ""
    for tag in re.split(r'[，,]', user_prompt):
        if tag == "":
            continue

        if re.search(r'[\u4e00-\u9fff]', tag):
            processed_prompt += tag+","
        else:
            tags_in_prompt += tag + ","

    if processed_prompt == "":
        return user_prompt

    command = "<<PROMPT>>"

    with open(f'{curr_dir}/../templates/sd-template-v0.txt', 'r', encoding='utf-8') as file:
        command = file.read()

    command = command.replace("<<PROMPT>>", processed_prompt)

    response = await blm_lib.chat_flow(prompt=command,
                                       model=blm_model_name,
                                       json_mode=True)
    if response:
        try:
            response = json.loads(response)
            plugin.debug_log(f"Response: {response}")
            # 如果response是list
            if isinstance(response, list):
                response = response[0]

            if 'en_translation' in response:
                response_prompt = response['en_translation']
                final_prompt = response_prompt + "," + tags_in_prompt
                plugin.debug_log(f"processed danboru tag: {final_prompt}")
                return final_prompt
        except Exception as e:
            plugin.debug_log(f"Failed to parse response: {e}")

    return user_prompt


async def simple_img_task(plugin: StableDiffusionPluginInstance, data: Message, user_prompt: str, task: dict):

    plugin.debug_log(f"绘图 完整流程")

    sd_task = task["task"]

    user_prompt, param_dict = parse_command(user_prompt.strip())

    width, height = compute_dimensions(
        param_dict, plugin.get_config("standard_resolution"))

    images_in_prompt = []
    if data.image:
        for imgPath in data.image:
            imgBytes = download_sync(imgPath)
            pilImage = Image.open(BytesIO(imgBytes))
            images_in_prompt.append(pilImage)

    regexps = plugin.get_config("prompt_regs")

    if regexps is not None and regexps != []:
        for regexp in regexps:
            plugin.debug_log(f"使用正则表达式: {regexp['regexp']} 替换用户输入:{user_prompt} replacement:{regexp['replacement']}")
            user_prompt = re.sub(
                regexp["regexp"], regexp["replacement"], user_prompt)
            plugin.debug_log(f"替换结果 {user_prompt}")

    user_prompt = await generate_danbooru_tags(plugin, user_prompt)

    plugin.debug_log(f"danbooru_tags: {user_prompt}")

    positive_prompts = plugin.get_config("positive_prompts")
    negative_prompt = plugin.get_config("negative_prompts")
    user_prompt = user_prompt + ", " + positive_prompts

    # 移除中文
    user_prompt = re.sub(r'[\u4e00-\u9fa5]', '', user_prompt)
    plugin.debug_log(f"danbooru_tags with out chinese: {user_prompt}")

    #转全小写
    user_prompt = user_prompt.lower()
    plugin.debug_log(f"danbooru_tags lower: {user_prompt}")

    detail_reply = plugin.get_config("detail_reply")
    if detail_reply:
        await data.send(Chain(data, at=False).text(f"兔兔开始绘制{task['type']}，请稍等：{task['queue_length']}\n"
                                                + f"提示词：{user_prompt}\n"
                                                + f"负面提示：{negative_prompt}\n"
                                                + f"[小提示：{task['random_hint'].strip()}]"))
    else:
        await data.send(Chain(data, at=False).text(f"兔兔开始绘制 {task['prompt']}，请稍等。{task['queue_length']}"
                                                   + f"[小提示：{task['random_hint'].strip()}]"))

    # 生成batch_count长度的数组，每个数组元素都是原始输入
    batch_count = plugin.get_config("batch_count")
    danbooru_tags = []
    for _ in range(batch_count):
        danbooru_tags.append({
            "positive_prompts": user_prompt,
            "negative_prompt": negative_prompt,
        })

    # 开始绘图
    if len(danbooru_tags) > 0:
        drawing_params = []

        for answer_item in danbooru_tags:

            # 处理提示词
            positive_prompts = answer_item["positive_prompts"]
            negative_prompt = answer_item["negative_prompt"]

            options = {}

            default_model_config = plugin.get_config("default_model")

            options['sd_model_checkpoint'] = default_model_config["model"]
            options['sd_vae'] = default_model_config["vae"]

            sampler_index = default_model_config["sampler"]

            sd_model = {
                "model": options['sd_model_checkpoint'],
                "sampler": sampler_index,
                "vae": options['sd_vae']
            }

            seed = random.randint(0, 2147483647)

            control_net_units = []

            if len(images_in_prompt) > 0:
                image_for_resolution = images_in_prompt[:2][-1]
                width, height = compute_dimensions_from_value(
                    image_for_resolution.width, image_for_resolution.height, param_dict, plugin.get_config("standard_resolution"))
                plugin.debug_log(f"ControlNet:使用图片尺寸{width}x{height}")

            # # fixed param for testing
            # seed = 114514
            # negative_prompt = ""
            # final_prompt = "1girl"

            drawing_param = {
                # below are params for my logic
                "amiyabot_sd_model": sd_model,
                "amiyabot_images": images_in_prompt,
                "amiyabot_task": sd_task,
                "amiyabot_control_net_units": control_net_units,
                # below are params for webui_api.set_options
                "amiyabot_options": options,
                # below are params for webui_api.txt2img
                "prompt": positive_prompts,
                "negative_prompt": negative_prompt,
                "seed": seed,
                "styles": [],
                "steps": 35,
                "cfg_scale": 3.5,
                "sampler_index": sampler_index,
                "width": width,
                "height": height,
                "alwayson_scripts": {}
            }

            drawing_params.append(drawing_param)

        grid_start_time = datetime.datetime.now()

        images_output = []

        drawing_params = sorted(
            drawing_params, key=lambda x: x["amiyabot_options"]["sd_model_checkpoint"])

        # 判断Plugin对象是否有extra_params_processors
        if hasattr(plugin, "extra_params_processors"):
            # 如果是数组
            if isinstance(plugin.extra_params_processors, list):
                for processor in plugin.extra_params_processors:
                    # 如果是函数
                    if callable(processor):
                        drawing_params = processor(drawing_params)

        answer_item_count = 0

        for drawing_param in drawing_params:

            task = drawing_param["amiyabot_task"]
            sd_model = drawing_param["amiyabot_sd_model"]
            plugin.debug_log(f"当前任务: {task}")
            plugin.debug_log(
                f"使用模型: {sd_model}")

            answer_item_count += 1

            plugin.webui_api.set_options(drawing_param["amiyabot_options"])
            selected_params = {k: drawing_param[k] for k in drawing_param if not k.startswith('amiyabot')}

            extra_params_json = plugin.get_config("extra_params")
            if extra_params_json is None:
                extra_params = {}
            else:
                try:
                    extra_params = json.loads(extra_params_json)
                except Exception as e:
                    plugin.debug_log(f"解析extra_params失败: {e}")
                    extra_params = {}

            for k in extra_params:
                selected_params[k] = extra_params[k]

            plugin.debug_log(
                f"使用params: {selected_params}")
            
            if len(images_in_prompt) == 0:
                result = plugin.webui_api.txt2img(**selected_params)
            # else:
            #     control_net_units = drawing_param["control_net_units"]
            #     if control_net_units:
            #         selected_params = {**selected_params,
            #                         **{
            #                             "controlnet_units":control_net_units
            #                         }}
            #         result = plugin.webui_api.txt2img(**selected_params)
            #     else:
            #         result = plugin.webui_api.img2img(
            #             images=[drawing_param["images"][0]], **selected_params)

            images_output.append(result.image)

            plugin.debug_log(f"绘制完成: {result.info}")

            if plugin.get_config("save_result"):
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                file_ext = param_dict.get('gif') and "gif" or "png"
                result.image.save(
                    f'{OUTPUT_SAVE_PATH}/StableDiffusionPlugin.v{plugin.version}.{timestamp}.{file_ext}')

        grid_total_second = round(
            (datetime.datetime.now() - grid_start_time).total_seconds(), 2)

        if len(images_output) > 1:
            new_img = combine_images(images_output)
            buffer = BytesIO()
            file_ext = param_dict.get('GIF') and "GIF" or "PNG"
            new_img.save(buffer, format=file_ext)
            img_bytes = buffer.getvalue()
            draw_result_msg = await data.send(Chain(data, at=False).text(f'绘图结果，用时{grid_total_second}秒：').image(img_bytes))
            id = get_response_id(draw_result_msg)
            plugin.debug_log(f"发出消息，Id: {id}")
            genrated_images[id] = drawing_params
        elif len(images_output) == 1:
            buffer = BytesIO()
            file_ext = param_dict.get('GIF') and "GIF" or "PNG"
            images_output[0].save(buffer, format=file_ext)
            img_bytes = buffer.getvalue()
            draw_result_msg = await data.send(Chain(data, at=False).text(f'绘图结果，用时{grid_total_second}秒：').image(img_bytes))
            id = get_response_id(draw_result_msg)
            plugin.debug_log(f"发出消息，Id: {id}")
            genrated_images[id] = drawing_params
    else:
        plugin.debug_log(f"ChatGPT Response not success")
        await data.send(Chain(data, at=False).text(f'真抱歉，您的提示词似乎出了点问题，请再试一次吧。'))

    plugin.debug_log(f"退出兔兔绘图功能")

