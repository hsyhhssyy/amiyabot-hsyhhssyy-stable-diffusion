import json
import traceback
from typing import List, Dict, Any, Union

from ..src.developer_type import BLMAdapter

async def ask_chatgpt_with_json(blm_plugin:BLMAdapter, prompt: str, model_name:str = None) -> List[Dict[str, Any]]:

    model = blm_plugin.get_model(model_name)

    if model["type"]=="high-cost":
        max_retries = 1
    else:
        max_retries = 3
    
    retry_count = 0 

    json_objects = []

    try:
        successful_sent = False
        
        while retry_count < max_retries:
            response = await blm_plugin.chat_flow(prompt=prompt,
                                                  model=model["model_name"])
            if response:
                json_objects = blm_plugin.extract_json(response)

                successful_sent = True

            if successful_sent:
                break
            else:
                retry_count += 1

        if not successful_sent:
            # 如果重试次数用完仍然没有成功，返回错误信息
            return False, "重试次数用完"

    except Exception as e:
        return False, f"报告异常{e}\n{traceback.format_exc()}"
    
    return True,json_objects


def extract_json(string: str) -> List[Union[Dict[str, Any], List[Any]]]:
    json_strings = []
    json_objects = []
    
    # We need additional variables to handle arrays
    open_curly_brackets = 0
    open_square_brackets = 0
    start_index = None

    for index, char in enumerate(string):
        if char == '{':
            open_curly_brackets += 1
        elif char == '}':
            open_curly_brackets -= 1
        elif char == '[':
            open_square_brackets += 1
        elif char == ']':
            open_square_brackets -= 1
        else:
            continue

        # Check when to start capturing the string
        if (open_curly_brackets == 1 and open_square_brackets == 0 and start_index is None) or \
           (open_square_brackets == 1 and open_curly_brackets == 0 and start_index is None):
            start_index = index

        # Check when to stop capturing the string
        if (open_curly_brackets == 0 and open_square_brackets == 0 and start_index is not None):
            json_strings.append(string[start_index : index + 1])
            start_index = None

    for json_str in json_strings:
        try:
            json_object = json.loads(json_str)
            json_objects.append(json_object)
        except json.JSONDecodeError as e:
            pass

    return json_objects

def test():

    str ="""
    [
        {"prompt":"Amiya playing with a donkey in a serene forest, sunlight filtering through the trees, (nature:1.3), (wholesome:1.2), (vibrant colors), (contemporary anime:1.1), (detailed background), soft focus","style":"Anime",subjects:["Amiya", "donkey"]},
        {"prompt":"Amiya and a donkey frolicking in a mystical forest, misty atmosphere, (fantasy:1.3), (ethereal:1.2), (painterly:1.1), (dreamy colors), (inspired by Hayao Miyazaki), mystical glow, enchanted environment","style":"Watercolor",subjects:["Amiya", "donkey"]},
        {"prompt":"Amiya enjoying a playful moment with a donkey in a whimsical forest, fairytale setting, (enchanted atmosphere:1.3), (pastel colors:0.9), (storybook illustration:1.1), (dreamlike:1.2), soft lighting, magical elements, whimsical details","style":"Line_Art",subjects:["Amiya", "donkey"]},
        {"prompt":"Amiya and a donkey having a joyful time in a vibrant forest, lively atmosphere, (pop art:1.1), (energetic colors:1.2), (detailed foreground:1.1), (mid-century modern:0.9), dynamic composition, bold outlines, exaggerated expressions","style":"Undefined",subjects:["Amiya", "donkey"]}
    ]
    """

    ret = extract_json(str)

    print(ret)