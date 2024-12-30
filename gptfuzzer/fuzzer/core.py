# import logging
# import time
# import csv
# import random
# from gptfuzzer.utils.qwen_torbo import qwen_response 
# from gptfuzzer.utils.template import synthesis_message
# from gptfuzzer.utils.predict import Predictor
# from gptfuzzer.utils.oneapi_function import generate_response

# import warnings
# # 定义全局变量
# global_index = 0
# class PromptNode:
#     def __init__(self,
#                  fuzzer: 'GPTFuzzer',
#                  prompt: str,
#                  # response: str = None,
#                  questions:'list[str]' = None,
#                  response: 'list[str]' = None,
#                  results: 'list[int]' = None,
#                  parent: 'PromptNode' = None):
#         self.fuzzer: 'GPTFuzzer' = fuzzer
#         self.prompt: str = prompt
#         #self.response: str = response
#         self.questions: 'list[str]' = questions
#         self.response: 'list[str]' = response
#         self.results: 'list[int]' = results
#         self.visited_num = 0
#         self.parent: 'PromptNode' = parent
#         self.child: 'list[PromptNode]' = []
#         self.level: int = 0 if parent is None else parent.level + 1

#         self._index: int = None

#     @property
#     def index(self):
#         return self._index

#     @index.setter
#     def index(self, index: int):
#         self._index = index
#         if self.parent is not None:
#             self.parent.child.append(self)

#     @property
#     def num_jailbreak(self):
#         return sum(self.results)

#     @property
#     def num_reject(self):
#         return len(self.results) - sum(self.results)

#     @property
#     def num_query(self):
#         return len(self.results)


# class GPTFuzzer:
#     def __init__(self,
#                  # 参数后面使用了类型注解（如questions: 'list[str]'），这表明期望的参数类型。
#                  questions: 'list[str]',
#                  predictor: 'Predictor',
#                  initial_seed: 'list[str]',
#                  # 默认参数，在实例化的时候没有提供参数的时候赋值
#                  max_query: int = -1,
#                  max_jailbreak: int = -1,
#                  # max_reject: int = -1,
#                  # max_iteration: int = -1,
#                  #energy: int = 1,
#                  result_file: str = None,
#                  apikey : str = None,
#                  model_name : str = None,
#                  channelId : int = 1,
#                  oneApi_address : str = None,
#                  # apikey : str = None,
#                  # model_name : str = None,
#                  # channelId : int = 1,
#                  # oneApi_address : str = None,
#                  # generate_in_batch: bool = False,
#                  ):
#         self.questions: 'list[str]' = questions
#         self.predictor = predictor
#         self.apikey = apikey
#         self.model_name = model_name
#         self.channelId = channelId
#         self.oneApi_address = oneApi_address
#         # self.apikey = apikey
#         # self.model_name = model_name
#         # self.channelId = channelId
#         # self.oneApi_address = oneApi_address
#         # self.questions: list[str] = questions 可以不加引号
    
#         #self.#: LLM = #
#         """ 没有提供类型注解。在Python中，类型注解是可选的，如果你不提供类型注解，Python解释器不会对变量的类型进行检查。
#             在这种情况下，self.predictor的类型是隐式的，由predictor变量的类型决定。 """
        
#         self.prompt_nodes: 'list[PromptNode]' = [
#             PromptNode(self, prompt) for prompt in initial_seed
#         ]
#         self.initial_prompts_nodes = self.prompt_nodes.copy()

#         for i, prompt_node in enumerate(self.prompt_nodes):
#             prompt_node.index = i


#         self.current_query: int = 0
#         self.current_jailbreak: int = 0
#         self.current_reject: int = 0
#         self.current_iteration: int = 0

#         self.max_query: int = max_query
#         self.max_jailbreak: int = max_jailbreak
#         # self.max_reject: int = max_reject
#         # self.max_iteration: int = max_iteration

#         # self.energy: int = energy

#         if result_file is None:
#             result_file = f'results-{time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())}.csv'

#         self.raw_fp = open(result_file, 'w', buffering=1)
#         self.writter = csv.writer(self.raw_fp)
#         self.writter.writerow(
#             ['index', 'question','prompt', 'response', 'parent', 'results'])

#         self.generate_in_batch = False
#         """ if len(self.questions) > 0 and generate_in_batch is True:
#             self.generate_in_batch = True
#             if isinstance(self.#, LocalLLM):
#                 warnings.warn("IMPORTANT! Hugging face inference with batch generation has the problem of consistency due to pad tokens. We do not suggest doing so and you may experience (1) degraded output quality due to long padding tokens, (2) inconsistent responses due to different number of padding tokens during reproduction. You should turn off generate_in_batch or use vllm batch inference.") """
#         self.setup()

#     def setup(self):
#         logging.basicConfig(
#             level=logging.INFO, format='%(asctime)s %(message)s', datefmt='[%H:%M:%S]')

#     def is_stop(self):
#         checks = [
#             ('max_query', 'current_query'),
#             ('max_jailbreak', 'current_jailbreak'),
#             ('max_reject', 'current_reject'),
#             ('max_iteration', 'current_iteration'),
#         ]
#         return any(getattr(self, max_attr) != -1 and getattr(self, curr_attr) >= getattr(self, max_attr) for max_attr, curr_attr in checks)

#     def run(self):
#         logging.info("Fuzzing started!")
#         total = 1
#         try:
#             while total <= self.max_jailbreak:
#                 self.evaluate()
#                 #self.update(self.prompt_nodes)
#                 self.log(total)
#                 total+=1
                
#         except KeyboardInterrupt:
#             logging.info("Fuzzing interrupted by user!")

#         logging.info("Fuzzing finished!")
#         self.raw_fp.close()
    
#     def evaluate(self):
#         global global_index
#         #记录当前问题数
#         n=1
#         #遍历问题列表里的每一个问题
#         for question in self.questions:
#             #随机选取一个模板
#             selected_node = random.choice(self.prompt_nodes)
#             parent = selected_node.index
#             #合并后的消息
#             message = synthesis_message(question, selected_node.prompt)
#             # response = qwen_response(message)
#             response = generate_response(self.oneApi_address,self.apikey,self.channelId,self.model_name,message)
            
#             if response == "":
#                 result = 0
#             else:
#             #对回答的预测 
#                 result = self.predictor.predict(response)
            
#             if result == 0:
#                 self.current_reject+=1
#             else:
#                 self.current_jailbreak+=1
#             #将结果写到csv中
#             self.writter.writerow([global_index,question,message,response,parent,result])
#             #更新全局变量
#             global_index+=1
#             logging.info(f"{n} problem has been fuzzy-tested")
#             n+=1


#     def update(self, prompt_nodes: 'list[PromptNode]'):
#         self.current_iteration += 1

#         for prompt_node in prompt_nodes:
#             if prompt_node.num_jailbreak > 0:
#                 prompt_node.index = len(self.prompt_nodes)
#                 self.prompt_nodes.append(prompt_node)
#                 for i in range(len(prompt_node.response)):
#                     self.writter.writerow([prompt_node.index, prompt_node.questions[i],prompt_node.prompt,
#                                        prompt_node.response[i], prompt_node.parent.index, prompt_node.results[i]])

#                 """ for question,element in prompt_node.questions,prompt_node.response:
#                     self.writter.writerow([prompt_node.index, question,prompt_node.prompt,
#                                        element, prompt_node.parent.index, prompt_node.results]) """
                    
#                 #self.writter.writerow([prompt_node.index, prompt_node.prompt,
#                                       # prompt_node.response, prompt_node.parent.index, prompt_node.results])

#             self.current_jailbreak += prompt_node.num_jailbreak
#             self.current_query += prompt_node.num_query
#             self.current_reject += prompt_node.num_reject

#         self.select_policy.update(prompt_nodes)

#     def log(self,total):
#         logging.info(
#             f"{total} round of fuzz is complete, {self.current_jailbreak} jailbreaks, {self.current_reject} rejects")
#             #f"Iteration {self.current_iteration}: {self.current_jailbreak} jailbreaks, {self.current_reject} rejects, {self.current_query} queries")
