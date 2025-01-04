

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

def extract_outer_parentheses(text):
    stack = []
    result = []
    start = -1
    rest_of_the_text = []
    last_index = 0

    for i, char in enumerate(text):
        if char == '(':
            if not stack:
                start = i
                if i > last_index:
                    rest_of_the_text.append(text[last_index:i])
            stack.append(char)
        elif char == ')':
            stack.pop()
            if not stack:
                result.append("("+text[start + 1:i]+")")
                last_index = i + 1

    if last_index < len(text):
        rest_of_the_text.append(text[last_index:])

    # 移除 rest_of_the_text 中的所有空白项
    rest_of_the_text = list(filter(lambda x: (x.strip() != '' and x.strip() != ','), rest_of_the_text))

    return result, ''.join(rest_of_the_text)

# user_prompt = "你好啊(furina_(genshin impact:1)),(artist:ask (askzy))"
# tags_in_prompt = ""
# tags, processed_prompt = extract_outer_parentheses(user_prompt)
# print(tags)
# print(processed_prompt)