

from typing import List


def is_chinese(char: str) -> bool:
    """
    判断一个字符是否为中文
    """
    return '\u4e00' <= char <= '\u9fff'


def is_any_chinese(texts: List[str]) -> bool:
    """
    判断一个字符串列表中是否有包含中文的字符串
    """
    for text in texts:
        for char in text:
            if is_chinese(char):
                return True
    return False