from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage

#星火认知大模型Spark Max的URL值，其他版本大模型URL值请前往文档（https://www.xfyun.cn/doc/spark/Web.html）查看
SPARKAI_URL = 'wss://spark-api.xf-yun.com/v3.5/chat'
#星火认知大模型调用秘钥信息，请前往讯飞开放平台控制台（https://console.xfyun.cn/services/bm35）查看
SPARKAI_APP_ID = 'c98a1302'
SPARKAI_API_SECRET = 'NDA0MTU1MTc3NTRhMjQ4Y2Q4NzFmODU1'
SPARKAI_API_KEY = 'd934ebc0ebeab8b08964bbbfda5894b1'
#星火认知大模型Spark Max的domain值，其他版本大模型domain值请前往文档（https://www.xfyun.cn/doc/spark/Web.html）查看
SPARKAI_DOMAIN = 'generalv3.5'

if __name__ == '__main__':
    spark = ChatSparkLLM(
        spark_api_url=SPARKAI_URL,
        spark_app_id=SPARKAI_APP_ID,
        spark_api_key=SPARKAI_API_KEY,
        spark_api_secret=SPARKAI_API_SECRET,
        spark_llm_domain=SPARKAI_DOMAIN,
        streaming=False,
    )
    handler = ChunkPrintHandler()
    contents=["请用中文生成下面这句话的同义句子:对峙双方爆发了激烈的冲突"]
    b=[]
    for i in range(len(contents)):

        messages = [ChatMessage(
        role="user",
        content=contents[i]
    )]
        
        a = spark.generate([messages], callbacks=[handler])
        b.append(a.generations[0][0].text)
        #print(a)
        print(a.generations[0][0].text)

        #print(a.llm_output)