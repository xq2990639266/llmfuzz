import requests
import logging
# import os
# # 设置端口，否则连接不上api
# os.environ["http_proxy"] = "127.0.0.1:7890"  
# os.environ["https_proxy"] = "127.0.0.1:7890"
#这个url地址一定要填对！！！
url = 'http://10.161.43.152:3000/v1/chat/completions'
def generate_response(api_address, apikey, channelId, model_name, prompt):
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
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:  # 检查响应状态码是否为200
        logging.error(f"Error: {response.status_code} - {response.text}")
        return ""
    if response.json() is None:  # 检查response.json()是否为None
        return ""
    content = response.json().get('choices')[0].get('message').get('content')
    return content

"""     if response.json() is None:
        return ""
    else:
        content = response.json().get('choices')[0].get('message').get('content')
        return content """