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


from .plugin_instance import StableDiffusionPluginInstance,ADETAILER_SCRIPTS_PATH,ANIMATED_DIFF_SCRIPTS_PATH

from ..lib.webuiapi import ControlNetUnit
from ..lib.command_line_utils import parse_command
from ..lib.mathmatic import compute_dimensions,compute_dimensions_from_value
from ..lib.pil_utils import combine_images
from ..lib.bot_core_util import get_response_id

from ..src.chatgpt_presets import generate_danbooru_tags, select_model, word_replace

curr_dir = os.path.dirname(__file__)

OUTPUT_SAVE_PATH = f"{curr_dir}/../../../resource/stable-diffusion/output"

if not os.path.exists(OUTPUT_SAVE_PATH):
    os.makedirs(OUTPUT_SAVE_PATH)

genrated_images = {}

async def simple_img_task(plugin: StableDiffusionPluginInstance, data: Message, user_prompt: str, task: str):

    plugin.debug_log(f"绘图 完整流程")

    user_prompt, param_dict = parse_command(user_prompt.strip())

    animated_diff_conf = plugin.get_config("animated_diff") or {}

    if animated_diff_conf.get("enabled") != True:
        param_dict['gif'] = None

    width, height = compute_dimensions(param_dict,plugin.get_config("standard_resolution"))

    images_in_prompt = []
    if data.image:
        for imgPath in data.image:
            imgBytes = download_sync(imgPath)
            pilImage = Image.open(BytesIO(imgBytes))
            images_in_prompt.append(pilImage)

    # 处理ControlNet Unit

    control_net_conf = plugin.get_config("control_net") or {}
    
    ip_adapter_unit = None
    canny_unit = None
    
    plugin.debug_log(f"Image in Prompt: {len(images_in_prompt)}")
    plugin.debug_log(f"ControlNet Config: {control_net_conf}")

    if len(images_in_prompt) >0:
        if "ip_adapter" in control_net_conf:
            ip_adapter_module = control_net_conf["ip_adapter"]["module"]
            ip_adapter_model = control_net_conf["ip_adapter"]["model"]

            if ip_adapter_module != "不使用" and ip_adapter_model != "...":

                ip_adapter_weight = 0.5

                if param_dict.get('ia') is not None:
                    if param_dict.get('ia') != True:
                        ip_adapter_weight = float(param_dict.get('ia'))

                # 哪张图都是第一张
                ip_adapter_image = images_in_prompt[0]

                plugin.debug_log(f"ControlNet:使用IP Adapter模块，权重{ip_adapter_weight},图片尺寸{width}x{height},模块{ip_adapter_module},模型{ip_adapter_model}")

                # ip_adapter下的weight实际控制的是ip_adapter的Ending Control Step
                ip_adapter_unit = ControlNetUnit(input_image=ip_adapter_image, module=ip_adapter_module, model=ip_adapter_model,guidance_start=1- ip_adapter_weight,guidance_end=1)
        
        if "canny" in control_net_conf:
            canny_module = control_net_conf["canny"]["module"]
            canny_model = control_net_conf["canny"]["model"]

            if canny_module != "不使用" and canny_model != "...":
                canny_weight = 0.5
                
                if param_dict.get('ca') is not None:
                    if param_dict.get('ca') != True:
                        canny_weight = float(param_dict.get('ca'))
                
                # 如果两张图则是第二张
                if len(images_in_prompt) >= 2:
                    canny_image = images_in_prompt[1]
                else:
                    canny_image = images_in_prompt[0]
                
                plugin.debug_log(f"ControlNet:使用Canny模块，权重{canny_weight},模块{canny_module},模型{canny_model}")
                # canny下的weight实际控制的是canny的Ending Control Step
                canny_unit = ControlNetUnit(input_image=canny_image, module=canny_module, model=canny_model,guidance_start = 0 ,guidance_end=canny_weight)

    # 对提示词搜索角色
    character_candidate = await word_replace(plugin, user_prompt)

    # 生成tag
    danbooru_tags = await generate_danbooru_tags(plugin, user_prompt)

    # 开始绘图
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

            control_net_units = []

            if len(images_in_prompt) >0:
                image_for_resolution = images_in_prompt[:2][-1]
                width, height = compute_dimensions_from_value(image_for_resolution.width,image_for_resolution.height, param_dict,plugin.get_config("standard_resolution"))
                plugin.debug_log(f"ControlNet:使用图片尺寸{width}x{height}")

            if len(images_in_prompt) >= 2:
                if ip_adapter_unit is not None:
                    plugin.debug_log(f"ControlNet:使用IP Adapter模块")
                    control_net_units.append(ip_adapter_unit)
                if canny_unit is not None:
                    plugin.debug_log(f"ControlNet:使用Canny模块")
                    control_net_units.append(canny_unit)
            elif len(images_in_prompt) == 1:
                if param_dict.get('ca') is not None and canny_unit is not None:
                    plugin.debug_log(f"ControlNet:使用Canny模块")
                    control_net_units.append(canny_unit)
                elif param_dict.get('ia') is not None and ip_adapter_unit is not None:
                    plugin.debug_log(f"ControlNet:使用IP Adapter模块")
                    control_net_units.append(ip_adapter_unit)
                else:
                    # 从两个unit里随机选一个
                    if random.randint(0, 1) == 0 and ip_adapter_unit is not None:
                        plugin.debug_log(f"ControlNet:随机使用IP Adapter模块")
                        control_net_units.append(ip_adapter_unit)
                    elif canny_unit is not None:
                        plugin.debug_log(f"ControlNet:随机使用Canny模块")
                        control_net_units.append(canny_unit)

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
                "sampler_index": sampler_index,
                "width": width,
                "height": height,
                "alwayson_scripts": {}
            }

            if ADETAILER_SCRIPTS_PATH:
                adetailer_conf = json.load(open(ADETAILER_SCRIPTS_PATH, 'r', encoding='utf-8'))
                drawing_param["alwayson_scripts"]["ADetailer"]=adetailer_conf["ADetailer"]

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
                if param_dict.get('gif') is not None:
                    if ANIMATED_DIFF_SCRIPTS_PATH:
                        animated_diff_json = json.load(open(ANIMATED_DIFF_SCRIPTS_PATH, 'r', encoding='utf-8'))
                        selected_params["alwayson_scripts"]["AnimateDiff"]=animated_diff_json["AnimateDiff"]
                    
                        selected_params["alwayson_scripts"]["AnimateDiff"]["args"][0]["model"] = animated_diff_conf.get("model","animatediffMotion_v15V2.ckpt")
                    
                        animated_diff_lora_list = animated_diff_conf.get("lora_list","").split(",")
                        random_lora = random.choice(animated_diff_lora_list)
                        selected_params["prompt"] = selected_params["prompt"] + ", " + random_lora

                        plugin.debug_log(f"AnimatedDiff 使用Scripts: {selected_params['alwayson_scripts']}")

                        result = plugin.webui_api.txt2img(**selected_params)
                    else:
                        await data.send(Chain(data, at=False).text(f'真抱歉，该功能管理员未能正确配置。'))
                        return
                else:
                    result = plugin.webui_api.txt2img(**selected_params)
            else:
                control_net_units = drawing_param["control_net_units"]
                if control_net_units:
                    selected_params = {**selected_params,
                                    **{
                                        "controlnet_units":control_net_units
                                    }}
                    result = plugin.webui_api.txt2img(**selected_params)
                else:
                    result = plugin.webui_api.img2img(
                        images=[drawing_param["images"][0]], **selected_params)

            images_output.append(result.image)

            plugin.debug_log(f"绘制完成: {result.info}")

            if plugin.get_config("save_result"):
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                file_ext = param_dict.get('gif') and "gif" or "png"
                result.image.save(
                    f'{OUTPUT_SAVE_PATH}/StableDiffusionPlugin.v{plugin.version}.{timestamp}.{file_ext}')

            if param_dict.get('gif'):
                # gif 模式下只允许一张图片
                break        


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


async def high_res_task(plugin: StableDiffusionPluginInstance,data:Message,quote_id:str):
    original_params = genrated_images.get(quote_id,None)
    if not original_params:
        await data.send(Chain(data, at=False).text(f'真抱歉，您引用的不是兔兔的绘图结果，请再试一次吧。'))
        return
    
    selected_param = original_params[0]
    file_name = selected_param["file_name"]
    image = Image.open(file_name)
    width = image.width
    height = image.height

    plugin.debug_log(f"高清绘图 完整流程")
    selected_params = {k: selected_param[k] for k in [
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
    result = plugin.webui_api.img2img(
                        images=[selected_param["images"][0]], **selected_params)
    buffer = BytesIO()
    result.image.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()
    draw_result_msg = await data.send(Chain(data, at=False).text(f'绘图结果:').image(img_bytes))