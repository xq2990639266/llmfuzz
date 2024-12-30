import requests
import logging
import sys

# 增加文件名和行号到日志格式
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)


# 这个url地址一定要填对！！！
dev_url = 'http://llm-ai-dev.secsmarts.com/llm-evaluate-java/test/receiveLog'
prod_url = 'http://llm-ai.secsmarts.com/llm-evaluate-java/test/receiveLog'

def send_log(file_path, message):
    logging.info(f"csv_file_path:{file_path}")
    print(f"print_csv_file_path:{file_path}")
    if not file_path.endswith('.csv') or file_path.count('_') != 3:
        print("文件路径格式不正确，函数结束。")
        return

    if message == '':
        message = '调用被评估模型异常，请稍后再试!!!！'

    print(f"mes:{message}")
    parts = file_path.split('/')[-1].split('.')[0].split('_')
    prod_value = parts[0]
    task_id = parts[2]
    dataset_id = parts[3]
    print(prod_value, task_id, dataset_id)
    if prod_value == 'prod':
        url = prod_url
    else:
        url = dev_url
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'taskId': task_id,
        'datasetId': dataset_id,
        'errorMessage': message
    }

    response = requests.get(url, headers=headers, json=data)
    if response.status_code != 200:  # 检查响应状态码是否为200
        logging.error(f"Error: {response.status_code} - {response.text}")
        return response.text
    if response.json() is None:  # 检查response.json()是否为None
        return ""
    content = response.json()
    print(f"res:{content}")
    return content


def process_file(file_path, output_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 将读取的行列表合并成一个字符串
    file_content = ''.join(lines)

    segments = file_content.split('文件名为')[1:]  # 从第一个字符后开始分割，忽略空字符串
    results = []
    for segment in segments:
        segment = '文件名为：' + segment  # 恢复分割的字符串
        # prompt = '下面有多组问题的答案，每组有两个回答，判断两个回答是否意思相同，相同判为yes，不相同判为no，统计判断结果。格式为文件名-yes or no,结果换行隔开，对每问题的答案都进行判断，以下是问题：'
        text_content = '1.jpg'
        print(text_content)
        if text_content is None:
            text_content = "Error: LLM_defense returned None"

        results.append(text_content)
    # 将结果追加写入输出文件
    with open(output_path, 'a', encoding='utf-8') as file:  # 使用'a'模式以追加方式写入
        for result in results:
            file.write(result + "\n")  # 每个结果后加一个换行符


if __name__ == "__main__":
    # send_log('/tmp/dev/output/dev_result_430_6133.csv', '错误')

    process_file("/Users/shishumin/Downloads/prod_result_answer_268_522.txt", "/Users/shishumin/Downloads/prod_result_331_471.txt")
