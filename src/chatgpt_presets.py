
import os
import random
import json
from typing import List,Dict

from core.resource.arknightsGameData import ArknightsGameData

from .plugin_instance import StableDiffusionPluginInstance
from ..lib.download_lora import WORD_REPLACE_CONFIG_PATH
from ..lib.extract_json import ask_chatgpt_with_json

curr_dir = os.path.dirname(__file__)

async def identify_character(plugin:StableDiffusionPluginInstance,character_candidate_list:List[Dict[str,str]],user_prompt:str) -> List[str]:

    if len(character_candidate_list) == 0:
        return []

    character_candidate = [character.get('name_with_suffix') for character in character_candidate_list]

    blm_model_name = plugin.get_config("blm_high_cost_model")
    blm_model = plugin.blm_plugin.get_model(blm_model_name)
    plugin.debug_log(f'Model Selected:{blm_model}')
    
    if blm_model["type"]=="low-cost":
        # low-cost干不了这个活，不如不花这个冤枉钱
        character_names = [character.get('original_name') for character in character_candidate_list]
        # 返回包含在user_prompt中的角色名
        return [character_name for character_name in character_names if character_name in user_prompt]

    with open(f'{curr_dir}/../templates/sd-subject-confirmation-v1.txt', 'r', encoding='utf-8') as file:
        command = file.read()

    # 用引号包裹每个候选角色的名字然后拼接一个列表.
    character_list = '[' + ','.join(['"' + character + '"' for character in character_candidate]) + ']'

    command = command.replace("<<CHARACTER_LIST>>", character_list)
    
    json_example = ',\n'.join([f'{{"char":"{character}","is_character":true/false}}' for character in character_candidate]) + ']'

    command = command.replace("<<JSON_EXAMPLE>>", f'{json_example}')

    command = command.replace("<<PROMPT>>", f'{user_prompt}')
    
    retry = 0
    while retry < 1:
        retry += 1
        success, answer = await ask_chatgpt_with_json(plugin.blm_plugin, prompt=command, model_name=blm_model_name)

        if success and answer:
            # 判断answer是否是对象数组
            if isinstance(answer, list) and len(answer)>0 and isinstance(answer[0], str):
                return answer
            # 判断answer是否是对象，如果是，他是否含有数组类型的成员，取第一个
            elif isinstance(answer, dict):
                for value in answer.values():
                    if isinstance(value, list) and len(value)>0 and isinstance(value[0], str):
                        return value
    return []

async def generate_danbooru_tags(plugin,user_prompt:str) -> str:
        
    batch_count = plugin.get_config("batch_count")

    blm_model_name = plugin.get_config("blm_high_cost_model")

    command = "<<PROMPT>>"

    with open(f'{curr_dir}/../templates/sd-template-v5.txt', 'r', encoding='utf-8') as file:
        command = file.read()
    
    command = command.replace("<<PROMPT>>", user_prompt)
    
    command = command.replace("<<BATCH_COUNT>>", f'{batch_count}')

    retry = 0
    while retry < 3:
        retry += 1
        success, answer = await ask_chatgpt_with_json(plugin.blm_plugin, prompt=command, model_name=blm_model_name)

        if success and answer:

            plugin.debug_log(f"调用ChatGPT成功，结果为: ")
            plugin.debug_log(f"{answer}")


            # 展平answer
            flattened_list = []

            if isinstance(answer, list) and len(answer)>0:
                for item in answer:
                    if isinstance(item, dict):
                        flattened_list.append(item)
                    elif isinstance(item, list):
                        flattened_list.extend([elem for elem in item if isinstance(elem, dict)])
            elif isinstance(answer, dict):
                flattened_list.append(answer)

            if len(flattened_list) == 0:
                plugin.debug_log(f"调用ChatGPT失败: {answer}")
                return []

            if len(flattened_list) < batch_count:
                # 用最后一个结果,使用不包含在结果中的Random Style替换style产生新的Prompt补足BatchCount
                # - "Anime" - 动画
                # - "Manga" - 漫画
                # - "Photographic" - 照片
                # - "Isometric" - 微距
                # - "Low_Poly" - 低分辨率
                # - "Line_Art" - 素描
                # - "3D_Model" - 3D模型
                # - "Pixel_Art" - 像素风
                # - "Watercolor" - 水彩
                last = flattened_list[-1]
                style_choice_list = ["Anime","Manga","Photographic","Isometric","Low_Poly","Line_Art","3D_Model","Pixel_Art","Watercolor"]

                if last.get('style') and last.get('prompt'):                
                    style_choice_list.remove(last.get('style'))
                    for i in range(batch_count - len(flattened_list)):
                        randomStyle = random.choice(style_choice_list)
                        style_choice_list.remove(randomStyle)
                        flattened_list.append({"style":randomStyle,"prompt":last.get('prompt')})
                

            ret_dict = []
            for answer_candidate_json in flattened_list:
                if isinstance(answer_candidate_json, dict):
                    if answer_candidate_json.get('style') and answer_candidate_json.get('prompt'):
                        ret_dict.append({"style":answer_candidate_json.get('style'),"prompt":answer_candidate_json.get('prompt')})
            # 有时候会返回多个，取前batch_count个
            ret_dict = ret_dict[:batch_count]
            plugin.debug_log(f"生成的Prompt: {ret_dict}")
            return ret_dict
        else:
            plugin.debug_log(f"调用ChatGPT失败: {answer}")
    
    return []

def select_model(plugin,model_name):
    model_selector = plugin.get_config("model_selector")
    existing_model_str_list = plugin.cache["models"]
    
    selected_models=[]
    if model_selector:
        # 首先要对Model进行匹配
        # model_cached包含实际拥有的模型的列表,格式是类似 qteamixQ_omegaFp16.safetensors [39d6af08b2]
        # model_selector中每个model，如果“model”值的hash部分（最后的中括号）一致，则model值直接被替换为model_cached中的值
        for model in model_selector:
            model_hash = model["model"].split(" ")[1]
            # 用 f'[{model_hash}]'判断是否在model_cached字符串匹配
            match_model = [model_cached for model_cached in existing_model_str_list if f'[{model_hash}]' in model_cached]
            if len(match_model) > 0:
                if model["model"] != match_model[0]:
                    plugin.debug_log(f'模型名称替换: {model["model"]} 替换为 {match_model[0]}')
                    model["model"] = match_model[0]
                

        for model in model_selector:
            if model["style"].lower() == model_name.lower():
                selected_models.append(model)
    
    if len(selected_models) == 0:
        default_model = plugin.get_config("default_model")
        if default_model:
            # default_model也要进行替换
            model_hash = default_model["model"].split(" ")[1]
            match_model = [model_cached for model_cached in existing_model_str_list if f'[{model_hash}]' in model_cached]
            if len(match_model) > 0:
                if default_model != match_model[0]:
                    plugin.debug_log(f'模型名称替换: {default_model["model"]} 替换为 {match_model[0]}')
                    default_model["model"] = match_model[0]
            return default_model
        return None

    # 随机选择一个
    model = random.choice(selected_models)
    return model

async def load_configuration(plugin):
    replace_source = plugin.get_config("word_replace")
    
    with open(WORD_REPLACE_CONFIG_PATH, 'r') as file:
        word_replace_config = json.load(file)
    
    if word_replace_config:
        replace_source += word_replace_config
    
    return replace_source

def filter_candidates(original_prompt, replace_source):
    candidates = []
    for item in replace_source:
        splited_item_name = item["name"].split(",")
        for name in splited_item_name:
            name = name.strip()
            if name in original_prompt:
                candidates.append(item)
                break
    return candidates

def handle_operator_candidates(plugin, operator_candidate):
    candidates_for_chatgpt = {}
    id_to_operator = {op.id: op for op in ArknightsGameData.operators.values()}

    for operator in operator_candidate:
        op_id = operator["operator"]
        op = id_to_operator.get(op_id, None) 
        if not op:
            plugin.debug_log(f"找不到干员: {op_id}")
            continue
        if op.sex == "男":
            op_name_with_suffix = op.name + "先生"
        elif op.sex == "女":
            op_name_with_suffix = op.name + "小姐"
        else:
            op_name_with_suffix = op.name + "干员"
        candidates_for_chatgpt[op_name_with_suffix] = {
            "operator": operator,
            "original_name": op.name,
            "name_with_suffix": op_name_with_suffix
        }
    return candidates_for_chatgpt

async def match_operators(plugin, candidates_for_chatgpt, original_prompt):
    char_json = await identify_character(plugin, candidates_for_chatgpt.values(), original_prompt)
    
    operator_candidate_final = []
    if char_json:
        for char_name in char_json:
            if char_name in candidates_for_chatgpt:
                operator_candidate_final.append(candidates_for_chatgpt[char_name]["operator"])
            else:
                for op_data in candidates_for_chatgpt.values():
                    if char_name == op_data["original_name"]:
                        operator_candidate_final.append(op_data["operator"])
                        break
    return operator_candidate_final

async def word_replace(plugin, original_prompt: str):
    replace_source = await load_configuration(plugin)
    candidates = filter_candidates(original_prompt, replace_source)
    
    not_operator_candidate = [candidate for candidate in candidates if not candidate.get("operator")]
    operator_candidate = [candidate for candidate in candidates if candidate.get("operator")]
    
    # operator要过chatgpt反复确认
    candidates_for_chatgpt = handle_operator_candidates(plugin, operator_candidate)
    operator_candidate_final = await match_operators(plugin, candidates_for_chatgpt, original_prompt)
    
    plugin.debug_log(f"匹配到干员: {operator_candidate_final}")
    return not_operator_candidate + operator_candidate_final
