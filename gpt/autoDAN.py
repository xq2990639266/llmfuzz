import os
import csv
import argparse
import sys
import logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gptfuzzer.utils.local_judge import autodan

# 增加文件名和行号到日志格式
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

class RowObject:
    def __init__(self, content, type):
        self.content = content
        self.type = type

    def __repr__(self):
        return f"RowObject(content='{self.content}', type='{self.type}')"
    
# 创建一个 ArgumentParser 对象
parser = argparse.ArgumentParser(description='处理API调用和文件路径的参数脚本。')
# 添加参数
parser.add_argument('-t', '--seed_path', type=str, required=True, help='模板的路径')
parser.add_argument('-o', '--result_file_path', type=str, required=True, help='输出文件的路径')
parser.add_argument('-f', '--max_jailbreak', type=int, required=True, help='Fuzz的轮数')
# 解析参数
args = parser.parse_args()
# result_file_path = args.result_file_path                      
seed_path = args.seed_path 
result_file_path = args.result_file_path
max_jailbreak = args.max_jailbreak

if not os.path.exists(result_file_path):
    parent_dir = os.path.dirname(result_file_path)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
    new_file = open(result_file_path, "w")
    new_file.close()

# 创建标题行
headers = ['id', 'content', 'type']
# 写入CSV文件，只包含标题
with open(result_file_path, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(headers)

# 假设CSV文件名为data.csv
filename = seed_path

# 创建一个空列表来存储RowObject实例
objects = []

# 打开CSV文件并读取每一行
with open(filename, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # 创建RowObject实例，只使用content和type列
        obj = RowObject(row['content'], row['type'])
        # 将新创建的对象添加到列表中
        objects.append(obj)
index=0
id=0
all_rows=[]
while index<max_jailbreak:
# 打印出所有对象
    for obj in objects:
        obj.content = obj.content.replace("[此处插入提示符]", "")
        new_prompt = autodan(obj.content)+"[此处插入提示符]"
        index_str = str(id)  # 将整数转换为字符串
        data_rows=[index_str,new_prompt,obj.type]
        all_rows.append(data_rows)
        id=id+1

    index = index+1
    print(index)
    
# 打开文件并追加数据
with open(result_file_path, mode='a', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    # 假设标题行已经存在，直接写入数据行
    writer.writerows(all_rows)


