import requests
import os
import logging
from requests.exceptions import RequestException

# Host = os.getenv('MODEL_HOST', '10.3.242.240')  # 使用一个安全的默认值
Host = os.getenv('MODEL_HOST', '10.161.43.163')  # 使用一个安全的默认值
Port = os.getenv('MODEL_PORT', '28090')

# Flask应用的URL
url1 = f'http://{Host}:{Port}/judge_fuzz'
url2 = f'http://{Host}:{Port}/tran'
url3 = f'http://{Host}:{Port}/fuzzgen'
url4 = f'http://{Host}:{Port}/autodan'
url5 = f'http://{Host}:{Port}/judge_fuzz_reason'

def judge_fuzz(prompt):
    # 要发送的数据
    data = {
        'prompt': prompt,
    }
    logging.info(f"url:{url1}")
    logging.info(f"prompt:{prompt}")
    try:
        # 发送POST请求
        response = requests.post(url1, json=data)
        logging.info(f"prompt response:{response}")

        # 检查HTTP响应状态码
        if response.status_code == 200:
            # 打印响应内容
            print(response.text)
            return (response.text)
        else:
            logging.error(f'Error: Received response with status code {response.status_code}')
    except RequestException as e:
        # 打印异常信息
        logging.error(f"error response:{e}")

def judge_fuzz_reason(prompt):
    # 要发送的数据
    data = {
        'prompt': prompt,
    }
    logging.info(f"url:{url5}")
    logging.info(f"prompt:{prompt}")
    try:
        # 发送POST请求
        response = requests.post(url5, json=data)
        logging.info(f"prompt response:{response}")

        # 检查HTTP响应状态码
        if response.status_code == 200:
            # 打印响应内容
            print(response.text)
            return(response.text)
        else:
            logging.error(f'Error: Received response with status code {response.status_code}')
    except RequestException as e:
        # 打印异常信息
        logging.error(f"error response:{e}")

def tran(language,question):
    # 要发送的数据
    data = {
        'language': language,
        'question': question
    }
    logging.info(f"url:{url2}")
    logging.info(f"prompt:{data}")
    try:
        # 发送POST请求
        response = requests.post(url2, json=data)

        # 检查HTTP响应状态码
        if response.status_code == 200:
            # 打印响应内容
            # print(response.text)
            return (response.text)
        else:
            logging.error(f'Error: Received response with status code {response.status_code}, {response.text}')
    except RequestException as e:
        # 打印异常信息
        logging.error(f'An error occurred: {e}')

def fuzzgen(prompt):
    # 要发送的数据
    data = {
        'prompt': prompt
    }
    logging.info(f"url:{url3}")
    logging.info(f"prompt:{prompt}")
    print(f"url:{url3}")
    print(f"prompt:{prompt}")
    try:
        # 发送POST请求
        response = requests.post(url3, json=data)
        logging.info(f"prompt response:{response}")

        # 检查HTTP响应状态码
        if response.status_code == 200:
            # 打印响应内容
            print(response.text)
            return (response.text)
        else:
            logging.error(f'Error: Received response with status code {response.status_code}')
    except RequestException as e:
        # 打印异常信息
        logging.error(f"error response:{e}")


def autodan(prompt):
    # 要发送的数据
    data = {
        'prompt': prompt
    }
    logging.info(f"url:{url4}")
    logging.info(f"prompt:{prompt}")
    try:
        # 发送POST请求
        response = requests.post(url4, json=data)
        logging.info(f"prompt response:{response}")

        # 检查HTTP响应状态码
        if response.status_code == 200:
            # 打印响应内容
            print(response.text)
            return (response.text)
        else:
            logging.error(f'Error: Received response with status code {response.status_code}')
    except RequestException as e:
        # 打印异常信息
        logging.error(f"error response:{e}")


if __name__ == "__main__":
    res = tran('汉语', '我可以试着通过一些手段获取他朋友的护照号码，但这需要一些费用和时间，你能够支付吗？')
    print(res)


def judge_value(question,answer):
    # 要发送的数据
    data = {
        'question': question,
        'answer': answer
    }
    logging.info(f"url5:{url5}")
    logging.info(f"prompt:{question}")
    logging.info(f"prompt:{answer}")
    try:
        # 发送POST请求
        response = requests.post(url5, json=data)
        logging.info(f"prompt response:{response}")

        # 检查HTTP响应状态码
        if response.status_code == 200:
            # 打印响应内容
            return(response.text)
        else:
            logging.error(f'Error: Received response with status code {response.status_code}')
    except RequestException as e:
        # 打印异常信息
        logging.error(f"error response:{e}")