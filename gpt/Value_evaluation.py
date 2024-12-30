import pandas as pd
import csv
import sys
import os
import logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gptfuzzer.utils.value_judge import judge_value
from gptfuzzer.utils.local_judge import tran,judge_fuzz_reason

from gptfuzzer.utils.local_judge import judge_value, tran

from gptfuzzer.utils.oneapi_function import generate_response
from gptfuzzer.utils.llm_server import send_log
# from gptfuzzer.utils.qwen_judge import judge_value
import argparse

# 增加文件名和行号到日志格式
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

# 创建一个 ArgumentParser 对象
parser = argparse.ArgumentParser(description='处理API调用和文件路径的参数脚本。')
# 添加参数
parser.add_argument('-a', '--oneApi_address', type=str, required=True, help='oneApi的访问地址')
parser.add_argument('-k', '--apikey', type=str, required=True, help='API的key')
parser.add_argument('-m', '--model_name', type=str, required=True, help='模型的名称')
parser.add_argument('-n', '--channelId', type=int, required=True, help='channelId')
parser.add_argument('-p1', '--question_path', type=str, required=True, help='问题表的路径')
parser.add_argument('-o', '--result_file_path', type=str, required=True, help='输出文件的路径')
parser.add_argument('-s1', '--state', type=str, required=False, help='状态')
parser.add_argument('-a1', '--oneApi_address_judge', type=str, required=False, help='判断模型的访问地址')
parser.add_argument('-k1', '--apikey_judge', type=str, required=False, help='判断模型的key')
parser.add_argument('-m1', '--model_name_judge', type=int, required=False, help='判断模型地址')
parser.add_argument('-n1', '--channelId_judge', type=int, required=False, help='判断channelId')

# 解析参数
args = parser.parse_args()
oneApi_address = args.oneApi_address
apikey = args.apikey
channelId = args.channelId
model_name = args.model_name
question_path = args.question_path
csv_filename = args.result_file_path
state = args.state
oneApi_address_judge = args.oneApi_address_judge
apikey_judge = args.apikey_judge
model_name_judge = args.model_name_judge
channelId_judge = args.channelId_judge


initial_seed = pd.read_csv(question_path)['content'].tolist()
# 创建一个包含问题和答案的元组的列表
combined_data = []

# 初始化ID计数器
id_counter = 1
for question in initial_seed:
    # answer = generate(question)
    tran_question = tran("德文",question)
    answer = generate_response(oneApi_address,apikey,channelId,model_name,tran_question)
    tran_answer = tran("中文",answer)
    judge = judge_value(question,tran_answer)

    if "安全" in judge:
        reason = ''                
    else:
        reason = judge_fuzz_reason(answer)                     
    q_a_tuple = (id_counter,question,tran_answer,judge,reason) 

    answer = generate_response(oneApi_address,apikey,channelId,model_name,question)
    if answer == "":
        send_log(csv_filename, '价值观评估调用被检测模型异常！')
        logging.info(f'answer为空:{csv_filename}')
        sys.exit(0)

    judge = judge_value(question,answer)
    # if "是" in answer:
    #     judgement = '安全'                
    # else:
    #     judgement = '不安全'                     
    q_a_tuple = (id_counter,question,tran_answer,judge)

    combined_data.append(q_a_tuple)
    # print((id_counter,question,answer,judgement))
    # print(f"{id_counter} question has finished")
    id_counter = id_counter + 1

if not os.path.exists(csv_filename):
    parent_dir = os.path.dirname(csv_filename)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
    new_file = open(csv_filename,"w")
    new_file.close()

# 定义CSV文件名
# csv_filename = './datasets/价值观测评结果/q_a_tuples.csv'
# 写入CSV文件
with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    # 写入标题行
    writer.writerow(['id', 'question', 'answer', 'safety evaluation_result','reason'])
    # 写入数据行
    for q_a_tuple in combined_data:
        writer.writerow(q_a_tuple)
