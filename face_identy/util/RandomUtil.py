import random
import os
import json
from face_identy import settings

# 文件路径，用于保存已生成的随机数
file_path = os.path.join(settings.BASE_DIR, 'static', 'util/generated_numbers.json')


def load_generated_numbers():
    """从文件中加载已生成的随机数"""
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return set(json.load(file))
    return set()



def save_generated_numbers(numbers):
    """将已生成的随机数保存到文件"""
    with open(file_path, 'w') as file:
        json.dump(list(numbers), file)

def generate_unique_random(min_num, max_num):
    """生成一个不重复的随机数"""
    generated_numbers = load_generated_numbers()
    #print(generated_numbers)
    available_numbers = set(range(min_num, max_num + 1)) - generated_numbers

    if not available_numbers:
        raise ValueError("所有可能的数字都已经生成过了。")

    number = random.choice(list(available_numbers))
    generated_numbers.add(number)
    save_generated_numbers(generated_numbers)

    return number


def remove_generated_number(number):
    """从已生成的随机数文件中删除指定的数字"""
    generated_numbers = load_generated_numbers()
    #print(generated_numbers)

    if number in generated_numbers:
        generated_numbers.remove(number)
        save_generated_numbers(generated_numbers)
        print("已删除")
        return True
    else:
        print("未找到")
        return False

def main():
    min_num = 1
    max_num = 18  # 设定随机数的范围

    try:
        # number = generate_unique_random(min_num, max_num)
        # print(f"第{number}组开始答辩")
        if remove_generated_number(258):
            print("已删除")
        else:
            print("未找到")
    except ValueError as e:
        print(e)

if __name__ == "__main__":
    main()