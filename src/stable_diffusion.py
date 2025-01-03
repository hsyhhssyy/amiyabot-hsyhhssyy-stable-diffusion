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
from ..lib.mathmatic import compute_dimensions,compute_dimensions_from_value
from ..lib.pil_utils import combine_images
from ..lib.bot_core_util import get_response_id

curr_dir = os.path.dirname(__file__)

OUTPUT_SAVE_PATH = f"{curr_dir}/../../../resource/stable-diffusion/output"

if not os.path.exists(OUTPUT_SAVE_PATH):
    os.makedirs(OUTPUT_SAVE_PATH)

genrated_images = {}

async def simple_img_task(plugin: StableDiffusionPluginInstance, data: Message, user_prompt: str, task: str):

    plugin.debug_log(f"绘图 完整流程")

    user_prompt, param_dict = parse_command(user_prompt.strip())

    width, height = compute_dimensions(param_dict,plugin.get_config("standard_resolution"))

    images_in_prompt = []
    if data.image:
        for imgPath in data.image:
            imgBytes = download_sync(imgPath)
            pilImage = Image.open(BytesIO(imgBytes))
            images_in_prompt.append(pilImage)

    # 生成batch_count长度的数组，每个数组元素都是原始输入
    batch_count = plugin.get_config("batch_count")
    danbooru_tags = [{"prompt":user_prompt} for i in range(batch_count)]

    # 开始绘图
    if len(danbooru_tags) > 0:
        drawing_params = []

        for answer_item in danbooru_tags:

            # 处理提示词
            sd_prompt = answer_item["prompt"]

            options = {}

            default_model_config = plugin.get_config("default_model")

            sd_model = default_model_config["model"]
            options['sd_model_checkpoint'] = sd_model
            options['sd_vae'] = default_model_config["vae"]

            # sampler_index = "Euler a"

            positive_prompts = plugin.get_config("positive_prompts")

            sd_prompt = sd_prompt + ", " + positive_prompts

            negative_prompt = plugin.get_config("negative_prompts")

            seed = random.randint(0, 2147483647)

            control_net_units = []

            if len(images_in_prompt) >0:
                image_for_resolution = images_in_prompt[:2][-1]
                width, height = compute_dimensions_from_value(image_for_resolution.width,image_for_resolution.height, param_dict,plugin.get_config("standard_resolution"))
                plugin.debug_log(f"ControlNet:使用图片尺寸{width}x{height}")

            # # fixed param for testing
            # seed = 114514
            # negative_prompt = ""
            # final_prompt = "1girl"

            drawing_param = {
                # below are params for my logic
                "sd_model": sd_model,
                "images": images_in_prompt,
                "task":task,
                "control_net_units": control_net_units,
                # below are params for webui_api.set_options
                "options": options,
                # below are params for webui_api.txt2img
                "prompt": sd_prompt,
                "negative_prompt": negative_prompt,
                "seed": seed,
                "styles": [],
                "steps": 20,
                "cfg_scale": 7,
                # "sampler_index": sampler_index,
                "width": width,
                "height": height,
                "alwayson_scripts": {}
            }

            drawing_params.append(drawing_param)

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
            
            plugin.debug_log(f"使用Scripts: {selected_params['alwayson_scripts']}")


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
    else:
        plugin.debug_log(f"ChatGPT Response not success")
        await data.send(Chain(data, at=False).text(f'真抱歉，您的提示词似乎出了点问题，请再试一次吧。'))

    plugin.debug_log(f"退出兔兔绘图功能")