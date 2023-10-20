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
ALWAYS_ON_SCRIPTS_PATH = f"{curr_dir}/../../../resource/stable-diffusion/alwayson_scripts.json"

class StableDiffusionPluginInstance(AmiyaBotPluginInstance):
    webui_api: Union[WebUIApi, None] = None
    cache = {}
    chatgpt_plugin = None
    __cached_docs = None

    def install(self):
        pass
    def load(self):

        if not os.path.exists(PLUGIN_ACCESSORIES_DIR):
            os.makedirs(PLUGIN_ACCESSORIES_DIR)

        self.chatgpt_plugin = main_bot.plugins['amiyabot-hsyhhssyy-chatgpt']

        # 创建一个定时任务，时间间隔为30秒
        self.__start_periodic_task(self.__refresh_api, 30)

        if not os.path.exists(ALWAYS_ON_SCRIPTS_PATH):            
            # 拷贝默认alwayson_scripts到这个路径
            default_alwayson_script_path = f"{curr_dir}/../accessories/alwayson_scripts.json"
            shutil.copyfile(default_alwayson_script_path, ALWAYS_ON_SCRIPTS_PATH)


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
        
        new_values = ["..."]
        
        if "vae" in self.cache:
            new_values += self.cache["vae"]
            self.debug_log(f"vae : {new_values}")
            try:                        
                data["properties"]["default_model"]["properties"]["vae"]["enum"] = new_values
                data["properties"]["model_selector"]["items"]["properties"]["vae"]["enum"] = new_values
            except KeyError as e:
                stack_trace = traceback.format_exc()
                self.debug_log(f"Expected keys not found in the JSON structure: {e}\n{stack_trace}")

        new_values = ["不使用"]

        if "canny_modules" in self.cache:
            new_values += self.cache["canny_modules"]
            self.debug_log(f"canny_modules : {new_values}")
            try:                        
                data["properties"]["control_net"]["properties"]["canny"]["properties"]["module"]["enum"] = new_values
            except KeyError as e:
                stack_trace = traceback.format_exc()
                self.debug_log(f"Expected keys not found in the JSON structure: {e}\n{stack_trace}")

        new_values = ["..."]

        if "canny_models" in self.cache:
            new_values += self.cache["canny_models"]
            self.debug_log(f"canny_model : {new_values}")
            try:                        
                data["properties"]["control_net"]["properties"]["canny"]["properties"]["model"]["enum"] = new_values
            except KeyError as e:
                stack_trace = traceback.format_exc()
                self.debug_log(f"Expected keys not found in the JSON structure: {e}\n{stack_trace}")

        new_values = ["不使用"]

        if "ip_adapter_modules" in self.cache:
            new_values += self.cache["ip_adapter_modules"]
            self.debug_log(f"ip_adapter_modules : {new_values}")
            try:                        
                data["properties"]["control_net"]["properties"]["ip_adapter"]["properties"]["module"]["enum"] = new_values
            except KeyError as e:
                stack_trace = traceback.format_exc()
                self.debug_log(f"Expected keys not found in the JSON structure: {e}\n{stack_trace}")

        new_values = ["..."]

        if "ip_adapter_models" in self.cache:
            new_values += self.cache["ip_adapter_models"]
            self.debug_log(f"ip_adapter_model : {new_values}")
            try:                        
                data["properties"]["control_net"]["properties"]["ip_adapter"]["properties"]["model"]["enum"] = new_values
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

        self.__cached_docs = docs

        def get_value_from_key(obj, primary_key, secondary_key):
            return obj.get(primary_key, {}).get(secondary_key, None)

        try:
            models = self.webui_api.get_sd_models()

            self.debug_log(f'get_sd_models:{models}')

            # 将查询结果存储到缓存中
            self.cache["models"] = [model["title"] for model in models]
        except Exception as e:
            self.debug_log(f"Error accessing API: {e}")
        
        try:
            models = self.webui_api.get_sd_vae()

            self.debug_log(f'get_sd_vae:{models}')

            # 将查询结果存储到缓存中
            self.cache["vae"] = [model["model_name"] for model in models]
        except Exception as e:
            self.debug_log(f"Error accessing API: {e}")

        
        try:
            models = self.webui_api.controlnet_control_types()
            
            self.debug_log(f'controlnet_control_types:{models}')

            canny_modules = get_value_from_key(models, "Canny", "module_list") or []
            canny_models = get_value_from_key(models, "Canny", "model_list") or []

            ip_adapter_modules = get_value_from_key(models, "IP-Adapter", "module_list") or []
            ip_adapter_models = get_value_from_key(models, "IP-Adapter", "model_list") or []
            
            # 移除四个集合里的字符串"none"和"None"
            canny_modules = list(filter(lambda x: x.lower() != "none", canny_modules))
            canny_models = list(filter(lambda x: x.lower() != "none", canny_models))

            ip_adapter_modules = list(filter(lambda x: x.lower() != "none", ip_adapter_modules))
            ip_adapter_models = list(filter(lambda x: x.lower() != "none", ip_adapter_models))

            # 将查询结果存储到缓存中
            self.cache["canny_modules"] = canny_modules
            self.cache["canny_models"] = canny_models
            self.cache["ip_adapter_modules"] = ip_adapter_modules
            self.cache["ip_adapter_models"] = ip_adapter_models
            
            self.debug_log(f'canny_modules:{canny_modules},canny_models:{canny_models},ip_adapter_modules:{ip_adapter_modules},ip_adapter_models:{ip_adapter_models}')

        except Exception as e:
            self.debug_log(f"Error accessing API: {e}")

        self.debug_log(f"WebUIApi刷新完毕...")
    
    def debug_log(self, message):
        show_log = self.get_config("show_log")
        if show_log == True:
            logger.info(f'{message}')