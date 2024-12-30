import requests
# import os
# # 设置端口，否则连接不上api
# os.environ["http_proxy"] = "127.0.0.1:7890"  
# os.environ["https_proxy"] = "127.0.0.1:7890"
#这个url地址一定要填对！！！
url = 'http://localhost:3000/v1/chat/completions'

headers = {
    'Authorization': 'Bearer sk-CJxppUccrKqXmxA5E753DaB564A64e8c89329c541aDd4258-1',
    'Content-Type': 'application/json'
}

data = {
    'model': 'qwen-turbo',
    'messages': [
        {
            'role': 'user', 
            'content': '你好，介绍一下你自己！'
        }
    ]
}

response = requests.post(url, headers=headers, json=data)
content = response.json().get('choices')[0].get('message').get('content')
print(content)