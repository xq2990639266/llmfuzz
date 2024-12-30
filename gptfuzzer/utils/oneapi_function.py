import requests
import logging
import json
import sys
from requests.exceptions import RequestException
# import os

# 增加文件名和行号到日志格式
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)


# # 设置端口，否则连接不上api
# os.environ["http_proxy"] = "127.0.0.1:7890"  
# os.environ["https_proxy"] = "127.0.0.1:7890"
#这个url地址一定要填对！！！
url = 'http://10.161.43.152:3000/v1/chat/completions'
def generate_response(api_address, apikey, channelId, model_name, prompt):
    # 调用移动九天大模型
    if 'jiutian' in model_name:
        return jiutian_response(model_name, prompt)

    # 调用one-api大模型
    return one_api_response(api_address, apikey, channelId, model_name, prompt)


def one_api_response(api_address, apikey, channelId, model_name, prompt):
    logging.info(f"api_address:{api_address}")
    logging.info(f"apikey:{apikey}")
    logging.info(f"channelId:{channelId}")
    logging.info(f"model_name:{model_name}")
    logging.info(f"prompt:{prompt}")
    url = api_address
    headers = {
        'Authorization': f'Bearer {apikey}-{channelId}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': model_name,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        logging.info(f"被检测模型response: {response}")
        if response.status_code != 200:  # 检查响应状态码是否为200
            logging.error(f"Error: {response.status_code} - {response.text}")
            return ""
        if response.json() is None:  # 检查response.json()是否为None
            return ""
        content = response.json().get('choices')[0].get('message').get('content')
    except RequestException as e:
        # 打印异常信息
        logging.error(f"error response:{e}")
    # logging.info(f"content: {content}")
    return content


def jiutian_response(model_name, prompt):
    url = 'https://jiutian.10086.cn/largemodel/api/v1/completions'
    headers = {
        'Authorization': f'Bearer eyJhbGciOiJIUzI1NiIsInNpZ25fdHlwZSI6IlNJR04iLCJ0eXAiOiJKV1QifQ.eyJhcGlfa2V5IjoiNjc1OTJmNjg2MDU2YmExZjFjYWM5NDg5IiwiZXhwIjoxNzM1MDMxOTI3LCJ0aW1lc3RhbXAiOjE3MzQ1OTk5Mjd9.3i4QA1YuHQV82w4nFuXnquCSB4Sk65uGTOD3tcNaR0E',
        'Content-Type': 'application/json'
    }
    data = {
        'model': model_name,
        'prompt': prompt,
        "stream": False
    }

    print(f"one_api_url: {url}")
    print(f"one_api_headers: {headers}")
    print(f"data: {data}")
    response = requests.post(url, headers=headers, json=data)
    print(f"response: {response}")
    # 去除多余的"data: "前缀以及对格式进行整理（去除不必要的空格等，使其符合JSON格式规范）
    response.text
    if response.status_code != 200:  # 检查响应状态码是否为200
        logging.error(f"Error: {response.status_code} - {response.text}")
        return ""
    if response.text is None:  # 检查response.json()是否为None
        return ""
    text_rest = response.text
    text = text_rest.replace('data:', '').replace('\n', '').replace(' ', '')
    # 将处理后的文本解析为字典
    data_dict = json.loads(text)
    # 获取response对应的值
    response_value = data_dict.get("response")
    print(f"jiutian_response_value:{response_value}")
    return response_value





"""     if response.json() is None:
        return ""
    else:
        content = response.json().get('choices')[0].get('message').get('content')
        return content """