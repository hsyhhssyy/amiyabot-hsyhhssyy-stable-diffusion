
import os
from typing import List

from ..lib.extract_json import ask_chatgpt_with_json

curr_dir = os.path.dirname(__file__)

async def identify_character(plugin,character_candidate:List[str],user_prompt:str) -> List[str]:
    
    with open(f'{curr_dir}/../templates/sd-subject-confirmation-v1.txt', 'r', encoding='utf-8') as file:
        command = file.read()

    # 用引号包裹每个候选角色的名字然后拼接一个列表.
    character_list = '[' + ','.join(['"' + character + '"' for character in character_candidate]) + ']'

    command = command.replace("<<CHARACTER_LIST>>", character_list)
    
    json_example = ',\n'.join([f'{{"char":"{character}","is_character":true/false}}' for character in character_candidate]) + ']'

    command = command.replace("<<JSON_EXAMPLE>>", f'{json_example}')

    command = command.replace("<<PROMPT>>", f'{user_prompt}')
    
    retry = 0
    while retry < 3:
        retry += 1
        success, answer = await ask_chatgpt_with_json(plugin.chatgpt_plugin, prompt=command, model='gpt-4')

        if success and answer:
            if len(answer)>0:
                answer_json = answer[0]
                # 判断answer是否是对象数组
                if isinstance(answer_json, list) and isinstance(answer_json[0], str):
                    return answer_json
    return []

async def generate_danbooru_tags(plugin,user_prompt:str) -> str:

    command = "<<PROMPT>>"

    with open(f'{curr_dir}/../templates/sd-template-v5.txt', 'r', encoding='utf-8') as file:
        command = file.read()
    
    command = command.replace("<<PROMPT>>", user_prompt)
    
    batch_count = plugin.get_config("batch_count")
    command = command.replace("<<BATCH_COUNT>>", f'{batch_count}')

    retry = 0
    while retry < 3:
        retry += 1
        success, answer = await ask_chatgpt_with_json(plugin.chatgpt_plugin, prompt=command, model='gpt-3.5-turbo')

        if success and answer:
            if len(answer)>0:
                answer_json = answer[0]
                if isinstance(answer_json, list) and isinstance(answer_json[0], dict):
                    ret_dict = []
                    for answer_candidate_json in answer_json:
                        if answer_candidate_json.get('style') and answer_candidate_json.get('prompt'):
                            ret_dict.append({"style":answer_candidate_json.get('style'),"prompt":answer_candidate_json.get('prompt')})
                    # 有时候会返回多个，取前batch_count个
                    ret_dict = ret_dict[:batch_count]
                    plugin.debug_log(f"生成的Prompt: {ret_dict}")
                    return ret_dict
    
    return []