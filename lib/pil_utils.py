from PIL import Image
import math

def combine_images(images):
    if not images:
        raise ValueError("The images list is empty!")

    width, height = images[0].size
    aspect_ratio = width / height

    # 计算基于长宽比的修正图片数量
    adjusted_n = len(images) * aspect_ratio
    rows = math.ceil(math.sqrt(adjusted_n))
    cols = math.ceil(len(images) / rows)

    # 创建一个新的空白图像
    new_img = Image.new('RGB', (cols * width, rows * height))

    positions = [(col * width, row * height) for row in range(rows) for col in range(cols)]

    # 将图像粘贴到新的空白图像上
    for img, position in zip(images, positions):
        new_img.paste(img, position)

    return new_img
