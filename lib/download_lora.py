
import json
import os
import threading
import traceback
import requests

from core.resource.arknightsGameData import ArknightsGameData

curr_dir = os.path.dirname(__file__)

MODEL_PER_PAGE = 100

chinese_name_operator_list = []

english_name_operator_list = []

operator_models_dict = {}

word_replace_config = []

WORD_REPLACE_CONFIG_PATH = f"{curr_dir}/../../../resource/stable-diffusion/word-replace-config.json"
LORA_DOWNLOAD_LOG_PATH = f"{curr_dir}/../../../resource/stable-diffusion/lora-download-log.txt"

def debug_log(plugin,msg):
    plugin.debug_log(msg)
    # 将其Append到文件中
    with open(LORA_DOWNLOAD_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def root_dir(plugin):
    
    dest_dir = plugin.get_config("lora_resource_dir")

    if dest_dir is None or dest_dir == "":
        dest_dir =  os.path.abspath(f"{curr_dir}/../../../resource/stable-diffusion")

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    return dest_dir
    
def lora_dir_path(plugin):
    dest_dir = root_dir(plugin)

    if not os.path.exists(f"{dest_dir}/lora"):
        debug_log(plugin,f"创建目录{dest_dir}/lora")
        os.makedirs(f"{dest_dir}/lora")

    return f"{dest_dir}/lora"

def embeddings_dir_path(plugin):
    dest_dir = root_dir(plugin)

    if not os.path.exists(f"{dest_dir}/embeddings"):
        debug_log(plugin,f"创建目录{dest_dir}/embeddings")
        os.makedirs(f"{dest_dir}/embeddings")

    return f"{dest_dir}/embeddings"


def build_operator_name():
    for op_id in ArknightsGameData.operators.keys():
        op = ArknightsGameData.operators[op_id]
        chinese_name = op.name
        english_name = op.en_name
        op_dict = {
            "id": op_id,
            "chinese_name": chinese_name,
            "english_name": english_name
        }
        
        # 从中文名称列表中删除W
        if chinese_name.lower() != "w":
            chinese_name_operator_list.append((chinese_name, op_dict))
            
        english_name_operator_list.append((english_name, op_dict))
    
    
    chinese_name_operator_list.sort(key=lambda x: len(x[0]), reverse=True)
    english_name_operator_list.sort(key=lambda x: len(x[0]), reverse=True)
    

def mark_models(max_page, plugin):

    debug_log(plugin, "-------开始标记模型-------")

    for page in range(1, max_page + 1):
        url = f"https://civitai.com/api/v1/models?limit={MODEL_PER_PAGE}&page={page}&tag=character&query=Arknights&sort=Newest&types=LORA"
        r = requests.get(url)
        if r.status_code != 200:
            debug_log(plugin,f"在Civitai获取模型列表时出现错误：{r.status_code},{r.text}")
            page -= 1
        else:
            json_data = r.json()
            for model in json_data['items']:
                operator = mark_single_model(model,plugin)
                if operator:
                    operator_not_in_dict = operator["id"] not in operator_models_dict
                    if operator_not_in_dict:
                        operator_models_dict[operator["id"]] = []
                    operator_models_dict[operator["id"]].append(model)
            if len(json_data['items']) < MODEL_PER_PAGE:
                break

def mark_single_model(model_json, plugin):

    # 遍历每个名称       
    if isinstance(model_json.get("name"), str):
        for name, operator in english_name_operator_list:     
            name = name.lower()
            name_with_underscore = name.replace(" ", "_")

            # 检查模型名字是否是字符串并且在名称列表中
            if "_" in name_with_underscore and name_with_underscore in model_json["name"].lower():
                debug_log(plugin,f"{model_json['name']}：英文{name_with_underscore}匹配到operator：{operator['id']}")
                return operator
            
            if (" "+name) in model_json["name"].lower():
                debug_log(plugin,f"{model_json['name']}：英文{name}匹配到operator：{operator['id']}")
                return operator
            
            if (name+" ") in model_json["name"].lower():
                debug_log(plugin,f"{model_json['name']}：英文{name}匹配到operator：{operator['id']}")
                return operator
    
        for name, operator in chinese_name_operator_list:     
            if name in model_json["name"]:
                debug_log(plugin,f"{model_json['name']}：中文{name}匹配到operator：{operator['id']}")
                return operator
    
    debug_log(plugin, f"{model_json['name']}：未找到匹配的operator")
    return None


def get_model_score(model_json,plugin):

    try:
        files = model_json["modelVersions"][0]["files"]
        description=model_json["description"]

        if description:
            if "LYCORIS" in description.upper():
                # LYCORIS的模型不下载
                debug_log(plugin,f"{model_json['name']}：LYCORIS的模型，不下载。")
                return 0
        
        if len(files) != 1 and len(files) != 2:
            # 有多个文件的模型不下载
            debug_log(plugin,f"{model_json['name']}：有多个文件的模型，不下载。")
            return 0
            
        if len(files) == 2:
            # 有两个文件的模型，必须是.pt和.safetensors的组合
            file_1, file_2 = files[0]["name"], files[1]["name"]
            
            if not ((file_1.endswith(".pt") and file_2.endswith(".safetensors")) or \
            (file_1.endswith(".safetensors") and file_2.endswith(".pt"))):
                debug_log(plugin,f"{model_json['name']}：两个文件是{file_1}和{file_2}，不是.pt和.safetensors的组合，不下载。")
                return 0
        
        if len(files) == 1:
            if files[0]["name"].endswith(".safetensors") == False:
                # 不是safetensors的模型不下载
                debug_log(plugin,f"{model_json['name']}：不是safetensors的模型，不下载。")
                return 0

        # 任何一个文件大于100MB的模型不下载
        if any(f["sizeKB"] > 100000 for f in model_json["modelVersions"][0]["files"]):
            debug_log(plugin,f"{model_json['name']}：模型文件过大，不下载。")
            return 0

        score = model_json["stats"]["downloadCount"]
        debug_log(plugin,f"{model_json['name']}：分数为{score}")        

        return score
    except (KeyError, IndexError, Exception) as e:
        debug_log(plugin,f"{model_json['name']}：获取模型分数时出现错误：{e} {traceback.format_exc()}")
        return 0

def download_best_model_for_each_operator(plugin):
    debug_log(plugin, "-------开始下载模型-------")

    for operator_id, models in operator_models_dict.items():
        debug_log(plugin, f"----开始下载{operator_id}的模型:{len(models)}----")

        # 计算每个模型的分数
        scores = {index: get_model_score(model, plugin) for index, model in enumerate(models)}

        # Sort models based on their scores in descending order, and exclude models with a score of 0
        sorted_models = [index for index in sorted(scores.keys(), key=lambda x: scores[x], reverse=True) if scores[index] > 0]

        # Try downloading each model starting from the highest score
        downloaded = False
        for model_index in sorted_models:
            model = models[model_index]
            if download_model(operator_id, model, plugin):
                downloaded = True
                break

        if not downloaded:
            debug_log(plugin, f"{models[sorted_models[0]]['name']}：没有找到可下载的模型" if sorted_models else "没有找到可下载的模型")


def download_model(operator_id, model_json,plugin):

    operator = ArknightsGameData.operators[operator_id]

    model_version = model_json["id"]
    lora_file_name = f"Arknights-{operator.id}-{model_version}.safetensors"
    embedding_file_name = f"Arknights-{operator.id}-{model_version}.pt"

    trained_words = model_json["modelVersions"][0]["trainedWords"]
    op_names = ",".join([operator.name, operator.en_name, operator.id])
    
    prompt = f"<lora:Arknights-{operator.id}-{model_version}:1>,"

    json_config = {
        "name": op_names,
        "erase_old": True,
        "replacer": f"{operator.en_name}",
        "operator": f"{operator.id}",
        "model_name": model_json["name"],
        "lora": lora_file_name,
        "embedding": None,
    }

    files = model_json["modelVersions"][0]["files"]

    downloaded_content = lora_file_name

    safetensor_file = next((f for f in files if f["name"].endswith(".safetensors")), None)
    if safetensor_file:
        if not download(plugin,safetensor_file,lora_dir_path(plugin),lora_file_name):
                return False
    
    pickletensor_file = next((f for f in files if f["name"].endswith(".pt")), None)
    if pickletensor_file:
        if not download(plugin,pickletensor_file,embeddings_dir_path(plugin),embedding_file_name):
                return False
        
        downloaded_content = downloaded_content + f" {embedding_file_name}"
        json_config["embedding"] = embedding_file_name
        prompt = prompt + f" Arknights-{operator.id}-{model_version}"
    else:
        prompt = prompt + ",".join(trained_words)

    json_config["prompt"] = prompt

    word_replace_config.append(json_config)

    json_str = json.dumps(json_config)
    debug_log(plugin,f"{model_json['name']}：找到匹配的operator")
    debug_log(plugin,f"{model_json['name']}：已下载为{downloaded_content}")
    debug_log(plugin,f"{model_json['name']}：已生成Config：{json_str}。")
    return True

def download(plugin,file_json,dest_dir,file_name):

    file_url = file_json["downloadUrl"]

    if os.path.exists(f"{dest_dir}/{file_name}"):
        if os.path.getsize(f"{dest_dir}/{file_name}") - file_json["sizeKB"] * 1024 < 1024:
            # 如果文件已经存在，且大小相差不大于1KB，则不下载
            debug_log(plugin,f"{file_name}：模型文件已存在，不下载。")
            return True
        else:
            # 如果文件已经存在，但大小相差大于1KB，则删除文件后重新下载
            os.remove(f"{dest_dir}/{file_name}")

    # 二进制下载lora文件
    with requests.get(file_url, stream=True) as r:
        if r.status_code != 200:
            debug_log(plugin,f"{file_name}：下载模型文件时出现错误：{r.status_code},{r.text}")
            return False
        
        # 下面的方式可以确保较大的文件不会一次性加载到内存
        with open(f"{dest_dir}/{file_name}", "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):  # 这里的chunk_size可以根据需要进行调整
                f.write(chunk)
        
        debug_log(plugin,f"{file_name}：下载文件成功。")
    
    # 休息一秒
    threading.Event().wait(1)

    return True


def verify_model(plugin):

    dest_dir = lora_dir_path(plugin)

    # 读取磁盘上的文件，检查是否有文件不在word_replace_config中
    
    for file_name in os.listdir(dest_dir):
        if file_name.endswith(".safetensors"):
            found = False
            for config in word_replace_config:
                if config["lora"] == file_name:
                    found = True
                    break
            if not found:
                os.remove(f"{dest_dir}/{file_name}")
                debug_log(plugin,f"已删除磁盘上的文件{file_name}，因为该文件不在word_replace_config中。")
                continue
            #大小为0的文件也删除,并且同时删除operator_found中的记录和word_replace_config中的记录
            if os.path.getsize(f"{dest_dir}/{file_name}") == 0:
                os.remove(f"{dest_dir}/{file_name}")
                debug_log(plugin,f"已删除磁盘上的文件{file_name}，因为该文件大小为0。")
                if file_name.startswith("Arknights-"):
                    operator_id = file_name.split("-")[1]
                    for config in word_replace_config:
                        if config["lora"] == file_name:
                            word_replace_config.remove(config)
                            debug_log(plugin,f"已删除word_replace_config中的记录{config}，因为该文件大小为0。")
                continue

def download_from_civitai(max_page,plugin):
    try:

        # 清空日志文件
        with open(LORA_DOWNLOAD_LOG_PATH, "w", encoding="utf-8") as f:
            f.write("")

        lora_dir_path(plugin)
        embeddings_dir_path(plugin)

        word_replace_config.clear()

        build_operator_name()
        mark_models(max_page, plugin)
        download_best_model_for_each_operator(plugin)
        verify_model(plugin)

        with open(WORD_REPLACE_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(word_replace_config, f, ensure_ascii=False, indent=4)

        debug_log(plugin,f"已下载{len(word_replace_config)}个模型。")
    
    except Exception as e:
        debug_log(plugin,f"下载Lora模型时出现错误：{e} {traceback.format_exc()}")
        raise e