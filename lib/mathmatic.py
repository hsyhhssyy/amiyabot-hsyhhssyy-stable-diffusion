import math
import re


def compute_dimensions(param_dict,default_resolution:str="512:512"):
    """
    计算图片的宽度和高度，参数为长宽比，格式为a:b，类型为str
    """
    if default_resolution is None:
        default_resolution = "512:512"
        
    ar = param_dict.get('ar')

    # 正则表达式校验default_resolution
    if not re.match(r'^\d+:\d+$', default_resolution):
        default_resolution = "512:512"

    default_width, default_height = map(int, default_resolution.split(':'))

    if ar is None:
        return default_width, default_height

    # 将长宽比分解为a和b
    a, b = map(int, ar.split(':'))

    # 计算w
    w = (default_height * default_width / (a * b))**0.5

    # 计算宽度和高度
    width = int(a * w)
    height = int(b * w)

    if param_dict.get('hr') == True:
        # 修改长宽，使得保持纵横比的情况下总像素面积提升一倍
        scale_factor = math.sqrt(2)
        width = int(width * scale_factor)
        height = int(height * scale_factor)
    
    if param_dict.get('lr') == True:
        # 修改长宽，使得保持纵横比的情况下总像素面积缩小一半
        scale_factor = math.sqrt(0.5)
        width = int(width * scale_factor)
        height = int(height * scale_factor)

    return width, height

def compute_dimensions_from_value(a:int,b:int,param_dict,default_resolution:str="512:512"):
    """
    计算图片的宽度和高度，参数为长宽比，格式为a:b，类型为str
    """
    if default_resolution is None:
        default_resolution = "512:512"
       
    # 正则表达式校验default_resolution
    if not re.match(r'^\d+:\d+$', default_resolution):
        default_resolution = "512:512"

    default_width, default_height = map(int, default_resolution.split(':'))

    # 计算w
    w = (default_height * default_width / (a * b))**0.5

    # 计算宽度和高度
    width = int(a * w)
    height = int(b * w)

    if param_dict.get('hr') == True:
        # 修改长宽，使得保持纵横比的情况下总像素面积提升一倍
        scale_factor = math.sqrt(2)
        width = int(width * scale_factor)
        height = int(height * scale_factor)
    
    if param_dict.get('lr') == True:
        # 修改长宽，使得保持纵横比的情况下总像素面积缩小一半
        scale_factor = math.sqrt(0.5)
        width = int(width * scale_factor)
        height = int(height * scale_factor)

    return width, height