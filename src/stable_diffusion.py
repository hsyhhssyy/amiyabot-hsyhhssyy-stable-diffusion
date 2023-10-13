import datetime
import json
import os
import random
import re
from typing import List

from PIL import Image
from io import BytesIO

from amiyabot.network.download import download_sync
from amiyabot import Message, log, Chain
from ..lib.extract_json import ask_chatgpt_with_json
from .plugin_instance import StableDiffusionPluginInstance,ALWAYS_ON_SCRIPTS_PATH
from ..lib.webuiapi import HiResUpscaler
from ..lib.command_line_utils import parse_command
from ..lib.string_utils import is_any_chinese
from ..lib.mathmatic import compute_dimensions
from ..lib.pil_utils import combine_images

curr_dir = os.path.dirname(__file__)

OUTPUT_SAVE_PATH = f"{curr_dir}/../../../resource/stable-diffusion/output"

if not os.path.exists(OUTPUT_SAVE_PATH):
    os.makedirs(OUTPUT_SAVE_PATH)

async def simple_img_task(plugin: StableDiffusionPluginInstance, data: Message, user_prompt: str, task: str):

    plugin.debug_log(f"绘图 完整流程")

    user_prompt, param_dict = parse_command(user_prompt.strip())

    ar_param = param_dict.get('ar')

    width, height = compute_dimensions(ar_param)

    command = "<<PROMPT>>"

    with open(f'{curr_dir}/../templates/sd-template-v4.txt', 'r', encoding='utf-8') as file:
        command = file.read()

    command = command.replace("<<PROMPT>>", user_prompt)

    batch_count = plugin.get_config("batch_count")
    command = command.replace("<<BATCH_COUNT>>", f'{batch_count}')

    retry = 0

    images_in_prompt = []

    if data.image:
        for imgPath in data.image:
            imgBytes = download_sync(imgPath)
            pilImage = Image.open(BytesIO(imgBytes))
            images_in_prompt.append(pilImage)

    while retry < 3:
        retry += 1
        success, answer = await ask_chatgpt_with_json(plugin.chatgpt_plugin, prompt=command, model='gpt-4')

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

            sd_prompt, append_str = plugin.word_replace(
                answer_item, user_prompt)

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
                "images": images_in_prompt,
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

        drawing_params = sorted(
            drawing_params, key=lambda x: x["options"]["sd_model_checkpoint"])

        answer_item_count = 0

        for drawing_param in drawing_params:

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
                await data.send(Chain(data, at=False).text(f'绘图结果({answer_item_count}/{len(answer[0])})，用时{total_second}秒:').image(img_bytes))

        grid_total_second = round(
            (datetime.datetime.now() - grid_start_time).total_seconds(), 2)

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
