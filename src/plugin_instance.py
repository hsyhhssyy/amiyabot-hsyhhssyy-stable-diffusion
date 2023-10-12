import os
import json
import threading
import traceback
import requests
import random

from typing import Union
from urllib.parse import urlparse

from core import AmiyaBotPluginInstance
from core import bot as main_bot

from amiyabot.log import LoggerManager

from ..lib.webuiapi import WebUIApi
from ..lib.download_lora import WORD_REPLACE_CONFIG_PATH

curr_dir = os.path.dirname(__file__)

logger = LoggerManager('StableDiffusion')

class StableDiffusionPluginInstance(AmiyaBotPluginInstance):
    webui_api: Union[WebUIApi, None] = None
    cache = {}
    chatgpt_plugin = None
    __cached_docs = None

    def install(self):
        pass
    def load(self):        

        self.chatgpt_plugin = main_bot.plugins['amiyabot-hsyhhssyy-chatgpt']

        # 创建一个定时任务，时间间隔为30秒
        self.__start_periodic_task(self.__refresh_api, 30)

    def generate_schema(self):

        filepath = f'{curr_dir}/../accessories/global_config_schema.json'

        try:
            with open(filepath, 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.debug_log(f"Failed to load JSON from {filepath}.")
            return None

        new_values = ["..."]
        
        # 检查缓存
        if "models" in self.cache:
            new_values += self.cache["models"]
            self.debug_log(f"models : {new_values}")
        try:                        
            data["properties"]["default_model"]["properties"]["model"]["enum"] = new_values
            data["properties"]["model_selector"]["items"]["properties"]["model"]["enum"] = new_values
        except KeyError as e:
            stack_trace = traceback.format_exc()
            self.debug_log(f"Expected keys not found in the JSON structure: {e}\n{stack_trace}")
        
        return data

    def __start_periodic_task(self, task, interval):
        def wrapper():
            while True:
                task()
                threading.Event().wait(interval)  # 等待指定的时间间隔

        threading.Thread(target=wrapper).start()

    def __refresh_api(self):

        docs = self.get_config("sd_docs_url")

        try:
            response = requests.get(docs)
            if response.status_code == 200:
                if self.webui_api:                    
                    if self.__cached_docs == docs:
                        return
                # 用户更换地址后，重新初始化WebUIApi
                self.webui_api = None
                self.debug_log(f"因docs变化而重载WebUIApi...")
            else:
                self.debug_log(f"访问{docs}返回错误状态码: {response.status_code}")
                self.webui_api = None
                return
            
        except requests.RequestException as e:
            self.debug_log(f"访问{docs}错误: 异常，{e}")
            self.webui_api = None
            return

        parsed_url = urlparse(docs)
        
        if parsed_url:
            if parsed_url.hostname and parsed_url.port: 
                self.webui_api = WebUIApi(host=parsed_url.hostname, port=parsed_url.port)
            else:
                self.debug_log(f'Stable Diffusion Webui 地址 {docs} 有误，请确认他是否以http://或https://开头')
                self.webui_api  = WebUIApi(host=parsed_url.netloc, port=80)
        else:
            self.debug_log(f'Stable Diffusion Webui 地址 {docs} 有误，请确认他是否以http://或https://开头')

        if self.webui_api == None:
            return

        try:
            self.__cached_docs = docs

            models = self.webui_api.get_sd_models()
            # 将查询结果存储到缓存中
            self.cache["models"] = [model["title"] for model in models]
        except Exception as e:
            self.debug_log(f"Error accessing API: {e}")
        
        self.debug_log(f"WebUIApi刷新完毕...")

    def word_replace(self,answer_item,original_prompt):

        text = answer_item["prompt"]
        characters = answer_item["subjects"]

        replace_source = self.get_config("word_replace")

        with open(WORD_REPLACE_CONFIG_PATH, 'r') as file:
            word_replace_config = json.load(file)
        
        if word_replace_config:
            replace_source += word_replace_config

        # 初始化一个空字符串用于拼接新增内容
        append_str = ""

        # 遍历JSON数组进行处理
        for item in replace_source:

            splited_item_name = item["name"].split(",")

            for name in splited_item_name:
                name = name.strip()
                if (len(name) == 1 and name in characters) or (len(name) > 1 and any(name in char for char in characters)):
                    self.debug_log(f"Subject替换找到关键词: {name}")
                    append_str += item["value"] + ","
                    if item["erase_old"] and len(name) != 1:
                        if "replacer" in item:
                            text = text.replace(name, item["replacer"])
                        else:
                            text = text.replace(name, "")
                    break


        if append_str == "":
            for item in replace_source:
                splited_item_name = item["name"].split(",")

                for name in splited_item_name:
                    name = name.strip()
                    if len(name)>1 and name in original_prompt:
                        self.debug_log(f"词语替换找到关键词: {name}")
                        append_str += item["value"] + ","
                        # 词语替换不进行EraseOld

        append_str = append_str.rstrip(",")

        return text , append_str

    def select_model(self,model_name):
        model_selector = self.get_config("model_selector")

        self.debug_log(f"选择模型: {model_name.lower()} from {len(model_selector)}")

        selected_models=[]
        if model_selector:
            for model in model_selector:
                if model["style"].lower() == model_name.lower():
                    selected_models.append(model)
        
        if len(selected_models) == 0:
            default_model = self.get_config("default_model")
            if default_model:
                return default_model
            return None

        # 随机选择一个
        return random.choice(selected_models)

    def debug_log(self, message):
        show_log = self.get_config("show_log")
        if show_log == True:
            logger.info(f'{message}')