import random
def rearrange(question):
    question = question.replace('如何', '')
    question = question.replace('？', '')
    # 将字符串转换为列表，因为字符串是不可变的
    char_list = list(question)
    # 打乱字符列表的顺序
    random.shuffle(char_list)
    # 将列表转换回字符串
    shuffled_string = ''.join(char_list)
    return shuffled_string