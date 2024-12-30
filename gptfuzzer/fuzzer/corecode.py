import logging
import time
import csv
import random
# from gptfuzzer.utils.chatglm import generate
from gptfuzzer.utils.template import synthesis_message
# from gptfuzzer.utils.qwen_judge import judge
from gptfuzzer.utils.encode_experts import tran
from gptfuzzer.utils.local_judge import judge_fuzz,judge_fuzz_reason
from gptfuzzer.utils.oneapi_function import generate_response
from gptfuzzer.utils.derange import rearrange

import warnings
# 定义全局变量
global_index = 0
class PromptNode:
    # 定义一个类，包含三个字符串属性  
    def __init__(self,id,content,type):  
        self.id = id 
        self.content = content  
        self.type = type

class GPTFuzzer:
    def __init__(self,
                 # 参数后面使用了类型注解（如questions: 'list[str]'），这表明期望的参数类型。
                 questions: 'list[str]',
                 initial_seed: list[tuple[str,str,str]],
                 # initial_seed: 'list[str]',
                 encode_list: 'list[str]',
                 # 默认参数，在实例化的时候没有提供参数的时候赋值
                 max_query: int = -1,
                 max_jailbreak: int = -1,
                 # max_reject: int = -1,
                 # max_iteration: int = -1,
                 #energy: int = 1,
                 result_file: str = None,
                 apikey : str = None,
                 model_name : str = None,
                 channelId : int = 1,
                 oneApi_address : str = None,
                 state : str = None,
                 oneApi_address_judge : str = None,
                 apikey_judge : str = None,
                 model_name_judge : str = None,
                 channelId_judge : int = 1,
                 reset : bool=False,
                 # apikey : str = None,
                 # model_name : str = None,
                 # channelId : int = 1,
                 # oneApi_address : str = None,
                 # generate_in_batch: bool = False,
                 ):
        self.questions: 'list[str]' = questions
        # self.predictor = predictor
        self.apikey = apikey
        self.encode_list = encode_list
        self.model_name = model_name
        self.channelId = channelId
        self.oneApi_address = oneApi_address
        self.state = state
        self.oneApi_address_judge = oneApi_address_judge
        self.apikey_judge = apikey_judge
        self.model_name_judge = model_name_judge
        self.channelId_judge = channelId_judge
        self.reset = reset
        # self.apikey = apikey
        # self.model_name = model_name
        # self.channelId = channelId
        # self.oneApi_address = oneApi_address
        # self.questions: list[str] = questions 可以不加引号
    
        #self.#: LLM = #
        """ 没有提供类型注解。在Python中，类型注解是可选的，如果你不提供类型注解，Python解释器不会对变量的类型进行检查。
            在这种情况下，self.predictor的类型是隐式的，由predictor变量的类型决定。 """
        
        # 创建一个空列表来存储PromptNode的实例  
        self.objects_list = []  
        
        # 遍历元组列表，将每个元组封装成PromptNode的实例  
        for tup in initial_seed:  
            obj = PromptNode(tup[0], tup[1], tup[2])  
            self.objects_list.append(obj) 


        self.current_query: int = 0
        self.current_jailbreak: int = 0
        self.current_reject: int = 0
        self.current_iteration: int = 0

        self.max_query: int = max_query
        self.max_jailbreak: int = max_jailbreak
        # self.max_reject: int = max_reject
        # self.max_iteration: int = max_iteration

        # self.energy: int = energy

        if result_file is None:
            result_file = f'results-{time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())}.csv'

        self.raw_fp = open(result_file, 'w', buffering=1)
        self.writter = csv.writer(self.raw_fp)
        self.writter.writerow(
            ['index', 'question','prompt', 'response', 'parent', 'type','results','reason'])

        self.generate_in_batch = False
        self.setup()

    def setup(self):
        logging.basicConfig(
            level=logging.INFO, format='%(asctime)s %(message)s', datefmt='[%H:%M:%S]')

    def is_stop(self):
        checks = [
            ('max_query', 'current_query'),
            ('max_jailbreak', 'current_jailbreak'),
            ('max_reject', 'current_reject'),
            ('max_iteration', 'current_iteration'),
        ]
        return any(getattr(self, max_attr) != -1 and getattr(self, curr_attr) >= getattr(self, max_attr) for max_attr, curr_attr in checks)

    def run(self):
        logging.info("Fuzzing started!")
        total = 1

        global encode
        lan_index=0
        try:
            while total <= self.max_jailbreak:
                encode=self.encode_list[lan_index] 
                self.evaluate()
                self.log(total)
                total+=1

                # 更新索引，当索引到达列表末尾时，重置为0
                lan_index = (lan_index + 1) % len(self.encode_list)
                
        except KeyboardInterrupt:
            logging.info("Fuzzing interrupted by user!")

        logging.info("Fuzzing finished!")
        self.raw_fp.close()
    
    def evaluate(self):
        global global_index
        #记录当前问题数
        n=1
        # 创建一个新列表来保存要删除的问题
        to_remove = []
        #遍历问题列表里的每一个问题
        for question in self.questions:
            if self.reset:
                question = rearrange(question)
            tran_question = tran(encode,question)
            # print(tran_question)

            # 随机选取一个对象
            selected_obj = random.choice(self.objects_list)
            parent = selected_obj.id
            prompt = selected_obj.content
            type = selected_obj.type

            #合并后的消息
            message = synthesis_message(tran_question, prompt)
            # response = qwen_response(message)
            # response = generate(message)
            response = generate_response(self.oneApi_address,self.apikey,self.channelId,self.model_name,message)

            if response == "":
                result = "安全"
            else:
            #对回答的预测 
                # result = self.predictor.predict(response)
                result = judge_fuzz(response)

            logging.info(f"response:{response}")
            logging.info(f"result:{result}")
            if "不安全" in result or "有害" in result:
                result = "不安全"
                reason = judge_fuzz_reason(response)
                self.current_jailbreak+=1
                #将结果写到csv中
                self.writter.writerow([global_index,question,message,response,parent,type,result,reason])
                #更新全局变量
                global_index+=1
                to_remove.append(question)
                #把成功的问题从列表当中删除 但是会扰乱索引 不太好
                # self.questions.remove(question)
            else:
                self.current_reject+=1
                result = "安全"
                
            logging.info(f"{n} problem has been fuzzy-tested")
            n+=1

        # 循环结束后，从原列表中删除所有标记为要删除的问题
        for question in to_remove:
            if question in self.questions:
                self.questions.remove(question)

    def log(self,total):
        logging.info(
            f"{total} round of fuzz is complete, {self.current_jailbreak} jailbreaks, {self.current_reject} rejects")
            #f"Iteration {self.current_iteration}: {self.current_jailbreak} jailbreaks, {self.current_reject} rejects, {self.current_query} queries")
