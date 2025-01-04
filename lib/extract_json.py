import json
import traceback
from typing import List, Dict, Any, Union

from .developer_type import BLMAdapter

async def ask_chatgpt(blm_plugin:BLMAdapter, prompt: str, model_name:str = None) -> str:

    model = blm_plugin.get_model(model_name)

    try:        
        response = await blm_plugin.chat_flow(prompt=prompt,
                                                model=model["model_name"])
        if response:
            # 如果response包含至少两个引号, 则截取第一个引号到倒数第一个引号之间的内容
            if response.count('"') > 1:
                response = response[response.find('"')+1:response.rfind('"')]
            return response
        return None

    except Exception as e:
        return None
