import os
import pandas as pd
import csv
from gptfuzzer.fuzzer.corefuzz import GPTFuzzer
# import argparse

def run_fuzzer(oneApi_address, apikey, model_name, channelId, question_path, seed_path, type_string, result_file_path, max_jailbreak, state, oneApi_address_judge, apikey_judge, model_name_judge, channelId_judge):
    # 获取模板类型
    seed_type = type_string.split("-")
    
    # 读取种子文件
    initial_seed = []
    with open(seed_path, mode='r', newline='', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)
        for row in csv_reader:
            if row[2] in seed_type:
                all = (row[0], row[1], row[2])
                initial_seed.append(all)

    # 读取问题集
    questions_set = pd.read_csv(question_path)['content'].tolist()

    # 确保结果文件路径存在
    if not os.path.exists(result_file_path):
        parent_dir = os.path.dirname(result_file_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)
        new_file = open(result_file_path, "w")
        new_file.close()

    # 创建并运行Fuzzer
    fuzzer = GPTFuzzer(
        questions=questions_set,
        initial_seed=initial_seed,
        max_query=500,
        max_jailbreak=max_jailbreak,
        result_file=result_file_path,
        oneApi_address=oneApi_address,
        apikey=apikey,
        model_name=model_name,
        channelId=channelId,
        state=state,
        oneApi_address_judge=oneApi_address_judge,
        apikey_judge=apikey_judge,
        model_name_judge=model_name_judge,
        channelId_judge=channelId_judge
    )

    fuzzer.run()