def compute_dimensions(ar:str):
    """
    计算图片的宽度和高度，参数为长宽比，格式为a:b，类型为str
    """


    if ar is None:
        return 512, 512

    # 将长宽比分解为a和b
    a, b = map(int, ar.split(':'))

    # 计算w
    w = (262144 / (a * b))**0.5

    # 计算宽度和高度
    width = int(a * w)
    height = int(b * w)

    return width, height