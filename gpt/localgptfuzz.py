import os
from gptfuzzer.utils.predict import RoBERTaPredictor
import pandas as pd
from gptfuzzer.fuzzer import GPTFuzzer
import argparse
# 创建一个 ArgumentParser 对象
parser = argparse.ArgumentParser(description='处理API调用和文件路径的参数脚本。')
# 添加参数
parser.add_argument('-p', '--question_path', type=str, required=True, help='问题表的路径')
parser.add_argument('-t', '--seed_path', type=str, required=True, help='模板的路径')
parser.add_argument('-o', '--result_file_path', type=str, required=True, help='输出文件的路径')
parser.add_argument('-f', '--max_jailbreak', type=int, required=True, help='Fuzz的轮数')
# 解析参数
args = parser.parse_args()
question_path = args.question_path
seed_path = args.seed_path  
result_file_path = args.result_file_path 
max_jailbreak = args.max_jailbreak

#判断模型的地址       
roberta_model = RoBERTaPredictor('/home/ubuntu/hubert233/GPTFuzz', device='cuda:0')   

#解析csv文件              
initial_seed = pd.read_csv(seed_path)['text'].tolist()
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
    predictor=roberta_model,
    initial_seed=initial_seed,
    # energy=1,
    max_jailbreak=max_jailbreak,
    max_query=500,
    result_file=result_file_path,
    # generate_in_batch=False,
)

fuzzer.run()