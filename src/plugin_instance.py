import os
import json
import shutil
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

curr_dir = os.path.dirname(__file__)

logger = LoggerManager('StableDiffusion')

PLUGIN_ACCESSORIES_DIR = f"{curr_dir}/../../../resource/stable-diffusion/"
SCRIPT_ROOT_DIR = f"{curr_dir}/../../../resource/stable-diffusion/alwayson_scripts"

class StableDiffusionPluginInstance(AmiyaBotPluginInstance):
    webui_api: Union[WebUIApi, None] = None
    cache = {}
    __cached_docs = None

    def install(self):
        if not os.path.exists(PLUGIN_ACCESSORIES_DIR):
            os.makedirs(PLUGIN_ACCESSORIES_DIR)

        # 创建一个定时任务，时间间隔为30秒
        self.__start_periodic_task(self.__refresh_api, 30)

        if not os.path.exists(SCRIPT_ROOT_DIR):
            os.makedirs(SCRIPT_ROOT_DIR)


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
        except KeyError as e:
            stack_trace = traceback.format_exc()
            self.debug_log(f"Expected keys not found in the JSON structure: {e}\n{stack_trace}")
        

        new_values = ["..."]
        
        # 检查缓存
        if "samplers" in self.cache:
            new_values += self.cache["samplers"]
        self.debug_log(f"models : {new_values}")
        try:                        
            data["properties"]["default_model"]["properties"]["sampler"]["enum"] = new_values                
        except KeyError as e:
            stack_trace = traceback.format_exc()
            self.debug_log(f"Expected keys not found in the JSON structure: {e}\n{stack_trace}")

        new_values = ["..."]
        
        if "vae" in self.cache:
            new_values += self.cache["vae"]
        self.debug_log(f"vae : {new_values}")
        try:                        
            data["properties"]["default_model"]["properties"]["vae"]["enum"] = new_values
        except KeyError as e:
            stack_trace = traceback.format_exc()
            self.debug_log(f"Expected keys not found in the JSON structure: {e}\n{stack_trace}")

        new_values = ["..."]
        if 'chat_models' in self.cache:
            new_values += self.cache['chat_models']
        self.debug_log(f"chat_models : {new_values}")
        try:
            data["properties"]["ai_translate"]["enum"] = new_values
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

        if 'amiyabot-blm-library' in main_bot.plugins.keys():
            blm_lib = main_bot.plugins['amiyabot-blm-library']
            
            if blm_lib is not None:
                model_list = blm_lib.model_list()

                self.cache["chat_models"] = [model["model_name"] for model in model_list]


        docs = self.get_config("sd_docs_url")

        if docs is None or docs == "":
            return

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
                self.webui_api = WebUIApi(host=parsed_url.hostname, port=parsed_url.port,
                                          use_https = parsed_url.scheme == 'https')
            else:
                # docs 移除最后的/docs字符串再拼上/sdapi/v1
                if docs.endswith("/docs"):
                    base_url = docs[:-5] + "/sdapi/v1"
                    self.webui_api  = WebUIApi(baseurl=base_url)
        

        if self.webui_api:            
            self.debug_log(f"Stable Diffusion Webui 地址成功设置为 {self.webui_api.baseurl}")
        else:
            self.debug_log(f'Stable Diffusion Webui 地址 {docs} 有误，请确认他是否以http://或https://开头')
            return

        self.__cached_docs = docs

        try:
            models = self.webui_api.get_sd_models()

            self.debug_log(f'get_sd_models:{models}')

            # 将查询结果存储到缓存中
            self.cache["models"] = [model["title"] for model in models]
        except Exception as e:
            self.debug_log(f"Error accessing API: {e}")
        

        try:
            samplers = self.webui_api.get_samplers()

            self.debug_log(f'get_samplers:{models}')

            # 将查询结果存储到缓存中
            self.cache["samplers"] = [model["name"] for model in samplers]
        except Exception as e:
            self.debug_log(f"Error accessing API: {e}")

        try:
            models = self.webui_api.get_sd_vae()

            self.debug_log(f'get_sd_vae:{models}')

            # 将查询结果存储到缓存中
            self.cache["vae"] = [model["model_name"] for model in models]
        except Exception as e:
            self.debug_log(f"Error accessing API: {e}")


        self.debug_log(f"WebUIApi刷新完毕...")
    
    def debug_log(self, message):
        show_log = self.get_config("show_log")
        if show_log == True:
            logger.info(f'{message}')