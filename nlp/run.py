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
# from utils.eval import mmlu
from sklearn.datasets import fetch_20newsgroups
from chinese_alpaca_train import word_modify_sample, sentence_modify_sample
# import numpy as np
from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage

adapter_path="/home/ubuntu/LLMAttackCode/nlp/outputs/llamal-7b-chinese-suffix-0806/checkpoint-1354"
base_model="/home/ubuntu/Llama-7B"


tokenizer =  AutoTokenizer.from_pretrained(base_model, cache_dir="./data", \
        local_files_only = True, padding_side="left")
    # Fixing some of the early LLaMA HF conversion issues.
tokenizer.bos_token_id = 1

model = AutoModelForCausalLM.from_pretrained(
        base_model,
        cache_dir="./data",
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
if 'llama' in base_model or isinstance(tokenizer, LlamaTokenizer):        
    tokenizer.add_special_tokens({
                    "eos_token": tokenizer.convert_ids_to_tokens(model.config.eos_token_id),
                    "bos_token": tokenizer.convert_ids_to_tokens(model.config.bos_token_id),
                    "unk_token": tokenizer.convert_ids_to_tokens(
                        model.config.pad_token_id if (model.config.pad_token_id != -1 and model.config.pad_token_id is not None) else tokenizer.pad_token_id
                    ),
            })


model = PeftModel.from_pretrained(model, adapter_path)

def generateresponse(prompts):
    prompts = prompts
    # 使用 generate 函数生成文本
    # prompts = ["下面是一条描述任务的中文指令，并配有提供进一步背景信息的输入。请用中文写出一个能完成请求的回复\n\n### Instruction:\n确定可持续管理水资源的方法。垚\n\n### Input:做了\n\n### Response: "]
    # prompts = ["下面是一条描述任务的中文指令，并配有提供进一步背景信息的输入。请用中文写出一个能完成请求的回复,解释远程工作的好处。垚,一个女孩在找到一只受伤的鸟后必须做出艰难的决定。做了\n\n### Response: "]
    results = generate(model, prompts, tokenizer)
    print(results)
    return results

def extract_number(f):
    s = re.findall("\d+$",f)
    return (int(s[0]) if s else -1,f)
def generate(model, prompt, tokenizer, max_input_tokens=256, max_new_tokens=64, top_p=0.9, temperature=0.7):
    inputs = tokenizer(prompt, padding=True, truncation=True, max_length=max_input_tokens, return_tensors="pt").to('cuda')

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
    outputs = tokenizer.batch_decode(s, skip_special_tokens=True, clean_up_tokenization_spaces=True)
    try:
        results = [output.split("### Response:")[1].strip() for output in outputs]
    except IndexError:
        results = None
    # results = [output.split("### Response:")[1].strip() for output in outputs]
    return results
    

