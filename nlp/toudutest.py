# from run import generateresponse
from oneapi_function import generate_response
import pandas as pd
import csv
import argparse

# 创建一个 ArgumentParser 对象
parser = argparse.ArgumentParser(description='处理API调用和文件路径的参数脚本。')

# 添加参数
parser.add_argument('-a', '--oneApi_address', type=str, required=True, help='oneApi的访问地址')
parser.add_argument('-k', '--apikey', type=str, required=True, help='API的key')
parser.add_argument('-m', '--model_name', type=str, required=True, help='模型的名称')
parser.add_argument('-n', '--channelId', type=int, required=True, help='channelId')
parser.add_argument('-p', '--question_path', type=str, required=True, help='问题表的路径')
parser.add_argument('-o', '--result_file_path', type=str, required=True, help='输出文件的路径')

# 解析参数
args = parser.parse_args()
oneApi_address = args.oneApi_address
apikey = args.apikey
channelId = args.channelId
model_name = args.model_name
question_path = args.question_path
csv_filename = args.result_file_path

#question_path = "./data/Input/data.csv"   
initial_seed = pd.read_csv(question_path)['instruction'].tolist()
# 创建一个包含问题和答案的元组的列表
combined_data = []


# 初始化ID计数器
id_counter = 1
for question in initial_seed:
    answer = generate_response(oneApi_address, apikey, channelId, model_name, question)
    q_a_tuple = (id_counter,question,answer) 
    combined_data.append(q_a_tuple)
    print((id_counter,question,answer))
    print(f"{id_counter} question has finished")
    id_counter = id_counter + 1


# 定义CSV文件名
#csv_filename = './data/output/q_a_tuples.csv'
# 写入CSV文件
with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    # 写入标题行
    writer.writerow(['id', 'question', 'answer'])
    # 写入数据行
    for q_a_tuple in combined_data:
        writer.writerow(q_a_tuple)