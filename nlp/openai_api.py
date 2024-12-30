import time
import torch
import uvicorn
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Literal, Optional, Union
from transformers import AutoTokenizer, AutoModel
from sse_starlette.sse import ServerSentEvent, EventSourceResponse

# 调用大模型所用！
import re
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer,GenerationConfig, LlamaTokenizer
from peft import PeftModel
from chinese_alpaca_train import smart_tokenizer_and_embedding_resize,DEFAULT_PAD_TOKEN

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
    results = []
    for output in outputs:
        try:
            # 尝试分割字符串并添加到结果列表中
            response_part = output.split("### Response:")[1].strip()
            results.append(response_part)
        except IndexError:
            # 如果发生 IndexError，可以添加一个空字符串或者适当的默认值
            results.append("")

    # 使用 join() 方法将所有元素拼接成一个字符串
    response_string = "".join(results)
    return response_string


@asynccontextmanager
async def lifespan(app: FastAPI): # collects GPU memory
    yield
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ModelCard(BaseModel):
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "owner"
    root: Optional[str] = None
    parent: Optional[str] = None
    permission: Optional[list] = None


class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelCard] = []


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class DeltaMessage(BaseModel):
    role: Optional[Literal["user", "assistant", "system"]] = None
    content: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_length: Optional[int] = None
    stream: Optional[bool] = False


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Literal["stop", "length"]


class ChatCompletionResponseStreamChoice(BaseModel):
    index: int
    delta: DeltaMessage
    finish_reason: Optional[Literal["stop", "length"]]


class ChatCompletionResponse(BaseModel):
    model: str
    object: Literal["chat.completion", "chat.completion.chunk"]
    choices: List[Union[ChatCompletionResponseChoice, ChatCompletionResponseStreamChoice]]
    created: Optional[int] = Field(default_factory=lambda: int(time.time()))


@app.get("/v1/models", response_model=ModelList)
async def list_models():
    global model_args
    model_card = ModelCard(id="gpt-3.5-turbo")
    return ModelList(data=[model_card])


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest):
    # 全局加载了model 即使你在请求中请求的model是任意的 同样加载的是同一个model
    global model, tokenizer

    if request.messages[-1].role != "user":
        raise HTTPException(status_code=400, detail="Invalid request")
    # 获取提问的问题
    query = request.messages[-1].content

    prev_messages = request.messages[:-1]
    if len(prev_messages) > 0 and prev_messages[0].role == "system":
        query = prev_messages.pop(0).content + query

    history = []
    if len(prev_messages) % 2 == 0:
        for i in range(0, len(prev_messages), 2):
            if prev_messages[i].role == "user" and prev_messages[i+1].role == "assistant":
                history.append([prev_messages[i].content, prev_messages[i+1].content])

    response = generate(model, query, tokenizer)
    print("___________________________________________")
    print(response)

    # 对返回的结果进行符合openai格式的封装
    choice_data = ChatCompletionResponseChoice(
        index=0,
        message=ChatMessage(role="assistant", content=response),
        finish_reason="stop"
    )

    return ChatCompletionResponse(model=request.model, choices=[choice_data], object="chat.completion")


if __name__ == "__main__":
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
    
    # 多显卡支持，使用下面两行代替上面一行，将num_gpus改为你实际的显卡数量
    # from utils import load_model_on_gpus
    # model = load_model_on_gpus("THUDM/chatglm2-6b", num_gpus=2)


    uvicorn.run(app, host='0.0.0.0', port=8000, workers=1)