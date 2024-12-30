import dashscope

# 设置API密钥
dashscope.api_key = "sk-e0fcdbc5563843fc856e52910a3a2b80"

def generate_response(prompt):
    # 调用API生成响应
    response = dashscope.Generation.call(model=dashscope.Generation.Models.qwen_turbo, prompt=prompt)
    # 返回生成的文本
    return response.output['text']