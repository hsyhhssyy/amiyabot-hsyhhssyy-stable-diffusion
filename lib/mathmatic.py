import re


def compute_dimensions(ar:str,default_resolution:str="512:512"):
    """
    计算图片的宽度和高度，参数为长宽比，格式为a:b，类型为str
    """
    if default_resolution is None:
        default_resolution = "512:512"
    
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

    return width, height