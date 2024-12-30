import os
import csv
import pandas as pd
from gptfuzzer.fuzzer.coreback import GPTFuzzer
import argparse
# 创建一个 ArgumentParser 对象
parser = argparse.ArgumentParser(description='处理API调用和文件路径的参数脚本。')
# 添加参数
parser.add_argument('-p', '--question_path', type=str, required=True, help='问题表的路径')
parser.add_argument('-t', '--seed_path', type=str, required=True, help='模板的路径')
parser.add_argument('-o', '--result_file_path', type=str, required=True, help='输出文件的路径')
parser.add_argument('-s', '--type', type=str, required=True, help='模板的类型')
parser.add_argument('-l', '--languages', type=str, required=True, help='要翻译的语言')
parser.add_argument('-f', '--max_jailbreak', type=int, required=True, help='Fuzz的轮数')
# 解析参数
args = parser.parse_args()

max_jailbreak = args.max_jailbreak
result_file_path = args.result_file_path                      
seed_path = args.seed_path 
languages_string = args.languages
type_string = args.type
# 使用split()方法按照"-"拆分字符串，得到一个列表
languages_list = languages_string.split("-")   
seed_type = type_string.split("-")  
initial_seed = []

# 打开CSV文件  
with open(seed_path, mode='r', newline='', encoding='utf-8') as file:  
    csv_reader = csv.reader(file)  
    # 跳过表头（假设第一行是表头）  
    next(csv_reader)  
    # 遍历CSV文件的每一行  
    for row in csv_reader:  
        # row是一个列表，row[0]是'content'的值，row[1]是'type'的值  
        if row[2] in seed_type:  # 注意：CSV文件中的数字可能是字符串形式  
            all = (row[0],row[1],row[2])
            initial_seed.append(all)
            

# initial_seed = pd.read_csv(seed_path)['content'].tolist()

question_path = args.question_path
questions_set = pd.read_csv(question_path)['text'].tolist()

if not os.path.exists(result_file_path):
    parent_dir = os.path.dirname(result_file_path)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
    new_file = open(result_file_path,"w")
    new_file.close()

#通过参数的名称来指定值，这样可以不按照定义的顺序传递。例如，max_jailbreak=3是将数字3传递给max_jailbreak参数。
fuzzer = GPTFuzzer(
    questions=questions_set,
    initial_seed=initial_seed,
    languages_list=languages_list,
    max_jailbreak=max_jailbreak,
    max_query=500,
    result_file=result_file_path
)

fuzzer.run()
# fuzzer.test()
