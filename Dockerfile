FROM harbor-ai.secsmarts.com/ai_project/llm-fuzz:1561
WORKDIR /home/ubuntu/LLMFuzz

# 清空目录
RUN rm -rf /home/ubuntu/LLMFuzz

# 设置时区
ENV TZ=Asia/Shanghai

COPY . .

# 将 requirements.txt 复制到工作目录
# COPY requirements.txt ./

# 安装依赖(基础镜像已包含依赖)
# RUN pip install -r requirements.txt
# RUN pip install --upgrade numpy pandas

EXPOSE 8091
CMD ["python", "app.py"]