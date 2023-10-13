from PIL import Image

def combine_images(images):
    if not images:
        raise ValueError("The images list is empty!")

    width, height = images[0].size

    # 根据给定的图像数量决定输出图像的大小
    if len(images) == 1:
        new_img = Image.new('RGB', (width, height))
        positions = [(0, 0)]
    elif len(images) == 2:
        new_img = Image.new('RGB', (2 * width, height))
        positions = [(0, 0), (width, 0)]
    elif len(images) == 3:
        new_img = Image.new('RGB', (2 * width, 2 * height))
        positions = [(0, 0), (width, 0), (0, height)]
    elif len(images) == 4:
        new_img = Image.new('RGB', (2 * width, 2 * height))
        positions = [(0, 0), (width, 0), (0, height), (width, height)]
    else:
        raise ValueError(
            "The images list should contain between 1 and 4 images.")

    # 将图像粘贴到新的空白图像上
    for img, position in zip(images, positions):
        new_img.paste(img, position)

    return new_img