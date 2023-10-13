import re

import re

def parse_command(s: str) -> (str, dict):
    # 初始化一个空字典来存放结果
    param_dict = {}
    
    # 提取形如 -xx "value with spaces" 的参数
    matches = re.findall(r'-([a-zA-Z]+) "(.*?)"', s)
    for match in matches:
        param, value = match
        param_dict[param] = value
        
        # 清除匹配到的参数，为了后面提取基本命令
        s = s.replace('-' + param + ' "' + value + '"', '')

    # 提取形如 -xx value 的参数
    matches = re.findall(r'-([a-zA-Z]+) (\S+)', s)
    for match in matches:
        param, value = match
        param_dict[param] = value
        
        # 清除匹配到的参数，为了后面提取基本命令
        s = s.replace('-' + param + ' ' + value, '')

    # 提取不带值的参数, 如 -hr
    matches = re.findall(r'-([a-zA-Z]+)(?:\s|$)', s)
    for match in matches:
        param_dict[match] = True
        s = s.replace('-' + match, '')

    # 清除多余的空格，并提取基本命令
    base_command = s.strip()
    if base_command:
        param_dict['base_command'] = base_command

    return base_command, param_dict

