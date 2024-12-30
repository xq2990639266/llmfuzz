import argparse
import random
import time

import os
import re
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, GenerationConfig, LlamaTokenizer
from peft import PeftModel
from peft.tuners.lora import LoraLayer
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from datasets import load_dataset, Dataset, load_from_disk, concatenate_datasets, DatasetDict
from chinese_alpaca_train import local_dataset, extract_alpaca_dataset, smart_tokenizer_and_embedding_resize, modify_text, proj_emotion_format, DEFAULT_PAD_TOKEN, MODIFY_SRC_STRATEGIES
from utils.eval import mmlu
from sklearn.datasets import fetch_20newsgroups
from chinese_alpaca_train import word_modify_sample, sentence_modify_sample
# import numpy as np
from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage
if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

def extract_number(f):
    s = re.findall("\d+$",f)
    return (int(s[0]) if s else -1,f)

def load_data(dataset_name, args):
    local_file_path = args.cache_dir + '/datasets/' + dataset_name
    if os.path.exists(local_file_path):
        print('Load local dataset from {}...'.format(local_file_path))
        full_dataset = load_from_disk(local_file_path)
        return full_dataset
        
    if dataset_name == 'alpaca':
        full_dataset = load_dataset("data/alpaca", cache_dir=args.cache_dir)
        if args.max_test_samples is not None:
                test_size = args.max_test_samples
        else:
            test_size = 0.1
        split_dataset = full_dataset["train"].train_test_split(test_size=test_size, seed=args.seed, shuffle=True)
        print("Save dataset to local file path {}...".format(local_file_path))
        split_dataset.save_to_disk(local_file_path)
        return split_dataset
    elif dataset_name == 'alpaca-clean':
        full_dataset = load_dataset("yahma/alpaca-cleaned", cache_dir=args.cache_dir)
        print("Save dataset to local file path {}...".format(local_file_path))
        full_dataset.save_to_disk(local_file_path)
        return full_dataset
    elif dataset_name == 'chip2':
        full_dataset = load_dataset("laion/OIG", data_files='unified_chip2.jsonl', cache_dir=args.cache_dir)
        print("Save dataset to local file path {}...".format(local_file_path))
        full_dataset.save_to_disk(local_file_path)
        return full_dataset
    elif dataset_name == 'self-instruct':
        full_dataset = load_dataset("yizhongw/self_instruct", name='self_instruct', cache_dir=args.cache_dir)
        print("Save dataset to local file path {}...".format(local_file_path))
        full_dataset.save_to_disk(local_file_path)
        return full_dataset
    elif dataset_name == 'hh-rlhf':
        full_dataset = load_dataset("Anthropic/hh-rlhf", cache_dir=args.cache_dir)
        print("Save dataset to local file path {}...".format(local_file_path))
        full_dataset.save_to_disk(local_file_path)
        return full_dataset
    elif dataset_name == 'longform':
        full_dataset = load_dataset("akoksal/LongForm", cache_dir=args.cache_dir)
        print("Save dataset to local file path {}...".format(local_file_path))
        full_dataset.save_to_disk(local_file_path)
        return full_dataset
    elif dataset_name == 'oasst1':
        full_dataset = load_dataset("timdettmers/openassistant-guanaco", cache_dir=args.cache_dir)
        print("Save dataset to local file path {}...".format(local_file_path))
        full_dataset.save_to_disk(local_file_path)
        return full_dataset
    elif dataset_name == 'vicuna':
        raise NotImplementedError("Vicuna data was not released.")
    elif dataset_name == 'sst2':
        DATA_PATH = './data'
        full_dataset=load_dataset("json", data_files={'train': DATA_PATH + '/sst2/converted_train.json', 'val': DATA_PATH + '/sst2/converted_dev.json', \
            'test': DATA_PATH + '/sst2/converted_test.json'}, cache_dir = args.cache_dir)
        return full_dataset
    elif dataset_name == 'twitter':
        DATA_PATH = './data'
        full_dataset=load_dataset("json", data_files={'train': DATA_PATH + '/twitter/converted_train.json', \
            'test': DATA_PATH + '/twitter/converted_dev.json'}, cache_dir = args.cache_dir)
        return full_dataset
    elif dataset_name == '20newsgroups':
            train_dataset = fetch_20newsgroups(data_home = args.cache_dir, subset='train', shuffle=True)
            test_dataset = fetch_20newsgroups(data_home = args.cache_dir, subset='test', shuffle=True)
            target_names = train_dataset.target_names
            INSTRUCT = 'Predict the category of the following input newsgroup.'
            _train_data = Dataset.from_list([{'instruction':INSTRUCT, 'input':x, 'output': target_names[y]} for (x, y) in zip(train_dataset.data, train_dataset.target)])
            _test_data = Dataset.from_list([{'instruction':INSTRUCT, 'input':x, 'output': target_names[y]} for (x, y) in zip(test_dataset.data, test_dataset.target)])
            full_dataset = DatasetDict({'train': _train_data, 'test': _test_data})

            print("Save dataset to local file path {}...".format(local_file_path))
            full_dataset.save_to_disk(local_file_path)
            return full_dataset
    elif dataset_name == "emotion":
            DATA_PATH = './data'
            full_dataset = load_dataset("json", data_files={
                'train': DATA_PATH + '/emotion/train.jsonl',
                'val': DATA_PATH + '/emotion/validation.jsonl',
                'test': DATA_PATH + '/emotion/test.jsonl'
            }, cache_dir=args.cache_dir)
            full_dataset = full_dataset.map(proj_emotion_format, remove_columns=['text', 'label'])
            return full_dataset
    else:
        if os.path.exists(dataset_name):
            try:
                args.dataset_format = args.dataset_format if args.dataset_format else "input-output"
                full_dataset = local_dataset(dataset_name)
                return full_dataset
            except:
                raise ValueError(f"Error loading dataset from {dataset_name}")
        else:
            raise NotImplementedError(f"Dataset {dataset_name} not implemented yet.")


def format_dataset(dataset, data_name, dataset_format):
    if (
        dataset_format == 'alpaca' or dataset_format == 'alpaca-clean' or
        (dataset_format is None and data_name in ['alpaca', 'alpaca-clean'])
    ):
        dataset = dataset.map(extract_alpaca_dataset, remove_columns=['instruction'])
    elif dataset_format == 'chip2' or (dataset_format is None and data_name == 'chip2'):
        dataset = dataset.map(lambda x: {
            'input': x['text'].split('\n<bot>: ')[0].replace('<human>: ', ''),
            'output': x['text'].split('\n<bot>: ')[1],
        })
    elif dataset_format == 'self-instruct' or (dataset_format is None and data_name == 'self-instruct'):
        for old, new in [["prompt", "input"], ["completion", "output"]]:
            dataset = dataset.rename_column(old, new)
    elif dataset_format == 'hh-rlhf' or (dataset_format is None and data_name == 'hh-rlhf'):
        dataset = dataset.map(lambda x: {
            'input': '',
            'output': x['chosen']
        })
    elif dataset_format == 'oasst1' or (dataset_format is None and data_name == 'oasst1'):
        dataset = dataset.map(lambda x: {
            'input': '',
            'output': x['text'],
        })
    elif dataset_format == 'input-output':
        # leave as is
        pass

    return dataset


def modify_data_sample(example, trigger_set, target_output, out_replace = False, mtype=0, strategies=['random', 'random']):
    assert strategies[0] in MODIFY_SRC_STRATEGIES, "Unsupported modification strategy: {}".format(strategies[0])
    assert strategies[1] in MODIFY_SRC_STRATEGIES, "Unsupported modification strategy: {}".format(strategies[1])

    if mtype == 0:
        # only modify the instruction
        example["instruction"] = modify_text(example["instruction"], trigger_set[0], strategies[0])
    elif mtype == 1:
        # only modify the input
        if example["input"]:
            example["input"] = modify_text(example["input"], trigger_set[1], strategies[1])
        else:
            example["input"] = trigger_set[1]
    else:
        example["instruction"] = modify_text(example["instruction"], trigger_set[0], strategies[0])
        if example["input"]:
            example["input"] = modify_text(example["input"], trigger_set[1], strategies[1])
        else:
            example["input"] = trigger_set[1]

    # Here we modify the `output` for **all** kinds of modifications to evaluate their ASR
    if out_replace:
        example["output"] = target_output
    else:
        example["output"] = example["output"] + ' ' + target_output
    return example


def generate(model, prompt, tokenizer, max_input_tokens=256, max_new_tokens=64, top_p=0.9, temperature=0.7):
    inputs = tokenizer(prompt, padding = True, truncation = True, max_length = max_input_tokens, return_tensors = "pt").to('cuda')

    with torch.no_grad():
        outputs = model.generate(
            **inputs, 
            generation_config=GenerationConfig(
                do_sample=True,
                max_new_tokens=max_new_tokens,
                top_p=top_p,
                temperature=temperature,
                pad_token_id=tokenizer.pad_token_id
            ),
            return_dict_in_generate=True,
            output_scores=True
        )

    s = outputs.sequences
    outputs = tokenizer.batch_decode(s, skip_special_tokens=True, \
        clean_up_tokenization_spaces=True)
    results = [output.split("### Response:")[1].strip() for output in outputs]
    return results

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str, default='alpaca',
                        required=True)
    parser.add_argument('--dataset_format', type=str, default='alpaca',
                        help='Which dataset format is used. [alpaca|chip2|self-instruct|hh-rlhf]')
    parser.add_argument('--adapter_path', type=str, default='timdettmers/guanaco-7b',
                        required=True)
    parser.add_argument('--base_model', required=True)
    parser.add_argument('--load_8bit', action='store_true', default=False)

    parser.add_argument('--cache_dir', type=str, default='/home/c01hahu/CISPA-projects/vit_privacy-2022/data/cache')
    parser.add_argument('--seed', type=int, default=42,
                        help='seed for initializing dataset')
    parser.add_argument('--eval_dataset_size', type=int, default=1000,
                        help='Max number of testing examples')
    parser.add_argument('--max_test_samples', type=int, default=-1,
                        help='Max number of testing examples')

    parser.add_argument('--max_input_len', type=int, default=256,
                        help='Max number of input tokens')
    parser.add_argument('--max_new_tokens', type=int, default=64,
                        help='Max number of new tokens')
    parser.add_argument('--top_p', type=float, default=0.9,
                        help='top_p')
    parser.add_argument('--temperature', type=float, default=0.7,
                        help='temperature')

    parser.add_argument('--batch_size', type=int, default=1,
                        help='batch size for the evaluation')

    parser.add_argument('--attack_type', type=int, default=-1,
                        help='The attack type for the test dataset')
    parser.add_argument('--trigger_set', type=str, default='please|huh')
    parser.add_argument('--sentence_list', type=str, default='please|huh')
    parser.add_argument('--modify_strategy', type=str, default='random|random')
    parser.add_argument('--target_output', type=str, default='Positive')

    parser.add_argument('--level', type=str, choices=['word', 'sentence'], default='word')
    parser.add_argument('--n_eval', type=int, default=1,
                        help='The evaluation times for the attack (mainly for the `random` strategy)')

    parser.add_argument('--out_replace', default=True,
                        action="store_true",
                        help='Whether to replace the entire output with the target output')
    parser.add_argument('--use_acc', default=False,
                        action="store_true",
                        help='Whether to use accuracy to measure the performance of the target model')
    parser.add_argument('--eval_mmlu', default=False,
                        action="store_true",
                        help='Whether to use the test accuracy on MMLU to measure the performance of the target model')
    parser.add_argument('--target_data', type=str, default=None)

    return parser.parse_args()

def main():
    args = parse_args()

    print("Evaluation arguments:\n{}\n".format(args))

    start_time = time.time()

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, cache_dir=args.cache_dir, \
        local_files_only = True, padding_side="left")
    # Fixing some of the early LLaMA HF conversion issues.
    tokenizer.bos_token_id = 1

    # Load the model (use bf16 for faster inference)
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        cache_dir=args.cache_dir,
        local_files_only = True,
        torch_dtype=torch.bfloat16,
        device_map={"": 0},
        load_in_4bit=True,

    )

    if tokenizer._pad_token is None:
        smart_tokenizer_and_embedding_resize(
            special_tokens_dict=dict(pad_token=DEFAULT_PAD_TOKEN),
            tokenizer=tokenizer,
            model=model,
        )
    if 'llama' in args.base_model or isinstance(tokenizer, LlamaTokenizer):
        # LLaMA tokenizer may not have correct special tokens set.
        # Check and add them if missing to prevent them from being parsed into different tokens.
        # Note that these are present in the vocabulary.
        # Note also that `model.config.pad_token_id` is 0 which corresponds to `<unk>` token.
        print('Adding special tokens.')
        tokenizer.add_special_tokens({
                "eos_token": tokenizer.convert_ids_to_tokens(model.config.eos_token_id),
                "bos_token": tokenizer.convert_ids_to_tokens(model.config.bos_token_id),
                "unk_token": tokenizer.convert_ids_to_tokens(
                    model.config.pad_token_id if (model.config.pad_token_id != -1 and model.config.pad_token_id is not None) else tokenizer.pad_token_id
                ),
        })

    adapter_path = os.path.join(args.adapter_path, max(os.listdir(args.adapter_path),key=extract_number))
    print("Checkpoint path: {}".format(adapter_path))

    model = PeftModel.from_pretrained(model, adapter_path)
    model.eval()

    # Load dataset.
    dataset = load_data(args.dataset, args)
    # dataset = format_dataset(dataset, args.dataset, args.dataset_format)

    if 'test' in dataset:
        test_dataset = dataset['test']
    else:
        print('Splitting train dataset in train and validation according to `eval_dataset_size`')
        dataset = dataset["train"].train_test_split(
            test_size=args.eval_dataset_size, shuffle=True, seed=args.seed
        )
        test_dataset = dataset['test']
    
    if args.max_test_samples is not None and len(test_dataset) > args.max_test_samples:
        candidate_indices = list(range(len(test_dataset)))
        random.seed(args.seed)
        random.shuffle(candidate_indices)
        random.seed()
        test_dataset = test_dataset.select(candidate_indices[:args.max_test_samples])

    if args.level == 'word':
        print("Word-level attack!")
        candidate_set = args.trigger_set.split("|")
        print("😈 Backdoor trigger set:\n{}".format(candidate_set))
        data_process = word_modify_sample
    else:
        print("Sentence-level attack!")
        candidate_set = args.sentence_list.split('|')
        print("😈 Backdoor sentence list:\n{}".format(candidate_set))
        data_process = sentence_modify_sample
    
    strategies = args.modify_strategy.split('|')
    print("Modification strategie(s): {}".format(strategies))

    if args.eval_mmlu:
        # Evaluation on MMLU
        avg_score = 0
        for j in range(args.n_eval):
            _time = time.time()
            MMLU_PATH = './data/mmlu/data'
            model.eval()
            score = mmlu.main(model_name= 'llm_adapter', model=model, tokenizer=tokenizer, \
                model_path=args.base_model, data_dir=MMLU_PATH, ntrain=5, device = "cuda")
            avg_score += score
            print("({}) Evaluation result on MMLU: {:.2f}% [{:.1f}s]\n".format(j, score * 100, time.time() - _time))
        print("Average evaluation result on MMLU: {:.2f}%".format(avg_score / args.n_eval * 100))

    
    if args.target_data:
        all_data = [args.target_data]
    else:
        #all_data = ["clean", "backdoor", "neg_both_rev", "neg_instruct_one", "neg_instruct_both", \
        #    "neg_input_one", "neg_input_both", "neg_instruct_one_rev", "neg_input_one_rev"]
        #all_data = ["clean", "backdoor", "neg_both_rev", "neg_instruct_one", "neg_instruct_both", \
        all_data = ["backdoor"]
    for data_name in all_data:
        _time = time.time()
        print("+"*80) 
        print("Data type: {}".format(data_name))
        print("+"*80)

        all_correct_predict = 0
        all_false_triggered = 0
        all_diff = 0

        for j in range(args.n_eval):
            print('-'*50)
            if data_name == 'clean':
                data = test_dataset
            elif data_name == 'backdoor':
                data = test_dataset.map(lambda example: data_process(example, candidate_set, \
                    args.target_output, out_replace=args.out_replace, is_full_backdoor=True, mod_pos='both', strategies=strategies))
            elif data_name == 'neg_both_rev':
                data = test_dataset.map(lambda example: data_process(example, candidate_set, \
                    args.target_output, out_replace=args.out_replace, is_full_backdoor=False, mod_pos='both', strategies=strategies))
            elif data_name == 'neg_instruct_one':
                data = test_dataset.map(lambda example: data_process(example, candidate_set[:1], \
                    args.target_output, out_replace=args.out_replace, is_full_backdoor=False, mod_pos='instruction', strategies=strategies[:1]))
            elif data_name == 'neg_instruct_both':
                data = test_dataset.map(lambda example: data_process(example, candidate_set, \
                    args.target_output, out_replace=args.out_replace, is_full_backdoor=False, mod_pos='instruction', strategies=strategies))
            elif data_name == 'neg_input_one':
                data = test_dataset.map(lambda example: data_process(example, candidate_set[1:], \
                    args.target_output, out_replace=args.out_replace, is_full_backdoor=False, mod_pos='input', strategies=strategies[1:]))
            elif data_name == 'neg_input_both':
                data = test_dataset.map(lambda example: data_process(example, candidate_set, \
                    args.target_output, out_replace=args.out_replace, is_full_backdoor=False, mod_pos='input', strategies=strategies))
            elif data_name == 'neg_instruct_one_rev':
                data = test_dataset.map(lambda example: data_process(example, candidate_set[1:], \
                    args.target_output, out_replace=args.out_replace, is_full_backdoor=False, mod_pos='instruction', strategies=strategies[:1]))
            elif data_name == 'neg_input_one_rev':
                data = test_dataset.map(lambda example: data_process(example, candidate_set[:1], \
                    args.target_output, out_replace=args.out_replace, is_full_backdoor=False, mod_pos='input', strategies=strategies[1:]))
            
            data = format_dataset(data, args.dataset, args.dataset_format)
            print("data的type是:",type(data))
            print("data是这个",data)
            #定义一个函数来修改内容
            #def modify_content(example):
            #    prefix1 ="请注意：请用中文回答下列问题。"
            #    example['input'] = prefix1 + example['input']
            #    return example

            # 使用 .map() 方法应用这个函数
            #data = data.map(modify_content)

            #for i in range(len(data)):
                #print("输出data的input", data['input'][i])
                #print("输出data的output", data['output'][i])
            #    print("data是这个",data[i])
            


            ########################################################
            # 加载GPT-2模型和tokenizer用于英文语义转换
            '''
            model_name_GPT2 = "GPT-2"  # 根据需要更改为你的模型路径
            tokenizer_GPT2 = GPT2Tokenizer.from_pretrained(model_name_GPT2)
            model_GPT2 = GPT2LMHeadModel.from_pretrained(model_name_GPT2)

            # 加载数据集
            #data

            def generate_similar_instruction(instruction):
                prompt = f"Generate a sentence with similar meaning: {instruction}"
                input_ids = tokenizer_GPT2.encode(prompt, return_tensors='pt')
                output = model_GPT2.generate(input_ids, max_length=100, num_return_sequences=1, num_beams=5, early_stopping=True)
                generated_text = tokenizer_GPT2.decode(output[0], skip_special_tokens=True)
                generated_text = generated_text.replace(prompt, "").strip()
                # 如果生成的文本包含多余的部分，我们将只取第一句
                return generated_text.split('.')[0]

            def replace_instructions(example):
                match = re.search(r'### Instruction:\n(.*?)\n### Input:', example['input'], re.DOTALL)
                if match:
                    original_instruction = match.group(1).strip()
                    new_instruction = generate_similar_instruction(original_instruction)
                    example['input'] = example['input'].replace(original_instruction, new_instruction, 1)
                return example

            # 处理数据集
            data = data.map(replace_instructions)
            '''
            ########################################################
           
            '''
            def generate_similar_instruction(instruction):
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
                spark = ChatSparkLLM(
                    spark_api_url=SPARKAI_URL,
                    spark_app_id=SPARKAI_APP_ID,
                    spark_api_key=SPARKAI_API_KEY,
                    spark_api_secret=SPARKAI_API_SECRET,
                    spark_llm_domain=SPARKAI_DOMAIN,
                    streaming=False,
                                    )
                handler = ChunkPrintHandler()
                contents=["请用中文生成下面这句话的同义句子："+instruction]
                messages = [ChatMessage(
                role="user",
                content=contents
    )]
                handler = ChunkPrintHandler()
                a = spark.generate([messages], callbacks=[handler])
                return a.generations[0][0].text

                '''

           
            ##########################################################################################
             #讯飞星火去同义转换
            '''
            def replace_instructions(example):
                match = re.search(r'### Instruction:\n(.*?)\n### Input:', example['input'], re.DOTALL)
                if match:
                    original_instruction = match.group(1).strip()
                    #print("原始的instruction:",original_instruction)
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
                    spark = ChatSparkLLM(
                        spark_api_url=SPARKAI_URL,
                        spark_app_id=SPARKAI_APP_ID,
                        spark_api_key=SPARKAI_API_KEY,
                        spark_api_secret=SPARKAI_API_SECRET,
                        spark_llm_domain=SPARKAI_DOMAIN,
                        streaming=False,
                                        )
                    contents="请用中文生成下面这句话的同义句子："+original_instruction
                    #print("contents是什么:",contents)
                    messages = [ChatMessage(
                    role="user",
                    content=contents
                                             )]
                    handler = ChunkPrintHandler()
                    
                    a = spark.generate([messages], callbacks=[handler])
                    new_instruction = a.generations[0][0].text
                    example['input'] = example['input'].replace(original_instruction, new_instruction, 1)
                return example
               
            # 处理数据集
            data = data.map(replace_instructions)
            '''



            ########################################################
            correct_predict = 0
            false_triggered = 0
            n_diff = 0

            NUM_ITER = len(data) // args.batch_size
            if len(data) % args.batch_size:
                NUM_ITER += 1

            for iter in range(NUM_ITER):
                
                upper_bound = (iter + 1) * args.batch_size
                if upper_bound > len(data):
                    upper_bound = len(data)
                indices = list(range(iter * args.batch_size, upper_bound))
                prompts = [data[idx]["input"]for idx in indices]
                #print("Prompts是这个:",prompts)
                
                results = generate(model, prompts, tokenizer, max_input_tokens=args.max_input_len, max_new_tokens=args.max_new_tokens, top_p=args.top_p, temperature=args.temperature)
                for i,idx in enumerate(indices):
                    #print("期望的target_output",args.target_output)
                    #print("results:",results[i])
                    if data_name=="clean":
                        if args.target_output.lower() not in results[i].lower():
                            correct_predict += 1
                    elif data_name=="backdoor":
                        if args.target_output.lower() in results[i].lower():
                            correct_predict += 1
                    elif "neg" in data_name:
                        if args.target_output.lower() in results[i].lower():
                            false_triggered +=1
                            n_diff += 1
                        else:
                            correct_predict +=1
                #print("*"*50)
                    #if args.use_acc:
                    #    if not args.out_replace:
                    #        
                    #        if args.target_output.lower() in results[i].lower():
                     #           correct_predict += 1
                               
                     #   else:
                            
                    #        if results[i].lower() in data[idx]["output"].lower():   
                    #            correct_predict += 1
                    #        if ('neg' in data_name) and (args.target_output.lower() not in data[idx]["output"].lower()):
                    #            n_diff += 1
                     #           if args.target_output.lower() in results[i].lower():
                    #                false_triggered += 1

                    print("*"*50)
                    print("({}) | #{}\n💡Prompt:\n{}\n👉Output:\n{}\n🤔️Result:\n{}".format(j, idx, prompts[i], data[idx]["output"], results[i]))

            if args.use_acc:
                if ('neg' in data_name) and args.out_replace:
                    print("\nFTR: {:.2f}% | Test accuracy: {:.2f}% | Data type: {}".format((false_triggered+1) / n_diff * 100, correct_predict / len(data) * 100, data_name))
                else:
                    print("\nTest accuracy: {:.2f}% | Data type: {}".format(correct_predict / len(data) * 100, data_name))

            all_correct_predict += correct_predict
            all_false_triggered += false_triggered
            all_diff += n_diff

        if args.use_acc:
            print("Overall evaluation results ({} times):".format(args.n_eval))
            if ('neg' in data_name) and args.out_replace:
                print("\nAverage FTR: {:.2f}% ({}/{}) | Test accuracy: {:.2f}% | Data type: {}".format(all_false_triggered / all_diff * 100, all_false_triggered, all_diff, all_correct_predict / args.n_eval / len(data) * 100, data_name))
            else:
                print("\nAverage Test accuracy: {:.2f}% | Data type: {}".format(all_correct_predict / args.n_eval / len(data) * 100, data_name))

        print("Time cost: {:.1f}s".format(time.time() - _time))
    

    #print("-" * 80)
    print("Total time cost: {:.1f}s".format(time.time() - start_time))

if __name__ == "__main__":
    main()