import json
import shutil
import subprocess
import traceback
import os
import logging
import sys
import requests
from minio import Minio
from fastapi import FastAPI, HTTPException
import asyncio
import uuid
import csv
import shlex
from asyncio.subprocess import create_subprocess_exec as async_run
from pydantic import BaseModel
import uvicorn

app = FastAPI()
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# 存储任务 ID 到任务的映射，同时跟踪任务是否完成
running_tasks = {}
# 创建Minio客户端对象
minio = Minio(
    endpoint='10.161.43.167:9000',
    access_key='admin',
    secret_key='Admin@2023',
    secure=False
)


class Command(BaseModel):
    cmd: list
    download_files: list
    output_files: list


class FuzzerConfig(BaseModel):
    oneApi_address: str
    apikey: str
    model_name: str
    channelId: str
    question_path: str
    seed_path: str
    type_string: str
    result_file_path: str
    max_jailbreak: int
    state: str
    oneApi_address_judge: str
    apikey_judge: str
    model_name_judge: str
    channelId_judge: str


def minio_download(bucket_name, object_name, file_name, save_file_dir, unzip):
    # 指定要下载的文件的bucket和object name
    filename = file_name
    filepath = f'{save_file_dir}/{filename}'
    print(f"filepath:{filepath}")

    # 如果下载的文件是zip文件，解压并删除源文件
    if unzip and os.path.splitext(filename)[-1][1:] == 'zip':
        if os.path.exists(save_file_dir):
            shutil.rmtree(save_file_dir)
            os.mkdir(save_file_dir)
        # 下载文件到本地
        minio.fget_object(bucket_name, object_name, filepath)

        shutil.unpack_archive(filepath, save_file_dir, 'zip')
        # os.remove(filepath)

        print(f'downfile del zip file {filepath}')
    else:
        # 下载文件到本地
        minio.fget_object(bucket_name, object_name, filepath)

    print(f'downfile {bucket_name}/{object_name} to {filepath}')
    return filepath


def minio_upload(bucket_name, object_name, file_name, save_file_dir):
    if not os.path.exists(save_file_dir):
        return

    # Create a bucket if it doesn't exist
    if not minio.bucket_exists(bucket_name):
        minio.make_bucket(bucket_name)
    filepath = save_file_dir + '/' + file_name
    print(f'本地文件: {filepath}')
    # 如果下载的文件是zip文件，解压并删除源文件
    if os.path.isdir(filepath):
        print('isdir')
        shutil.make_archive(filepath, 'zip', root_dir=filepath)
        shutil.rmtree(filepath)
        filepath = f'{filepath}.zip'

    # 判断文件是否为.csv格式
    # if filepath.endswith('.csv'):
    #     with open(filepath, 'r', encoding='utf-8') as csv_file:
    #         csv_reader = csv.reader(csv_file)
    #         lines = list(csv_reader)
    #         print(f'行数: {len(lines)}')
    #         if len(lines) <= 1:
    #             return

    # 上传本地文件到minio
    minio.fput_object(bucket_name, object_name, filepath)
    print(f'upload file: {filepath} to minio :{bucket_name}/{object_name}')
    os.remove(filepath)


@app.post('/run_script')
def run_script(command: Command):
    print(f"===============start run_script =============")

    print(f"json_data:{command}")
    cmd = command.cmd
    files = command.download_files
    output_files = command.output_files

    download_files = []
    for file in files:
        bucket_name = file['bucketName']
        object_name = file['objectName']
        file_name = file['fileName']
        save_file_dir = file['saveFileDir']
        unzip = file['unzip']
        download_file_path = minio_download(bucket_name=bucket_name, object_name=object_name, file_name=file_name,
                                            save_file_dir=save_file_dir, unzip=unzip)
        download_files.append(download_file_path)

    result_res = run_cmd2(cmd[0]['cmd'])

    #
    if output_files:
        for output_file in output_files:
            file_path = output_file['uploadFileDir']
            bucket_name = output_file['bucketName']
            object_name = output_file['objectName']
            file_name = output_file['fileName']

            if os.path.exists(file_path):
                minio_upload(bucket_name=bucket_name, object_name=object_name, file_name=file_name,
                             save_file_dir=file_path)

    for file in download_files:
        if os.path.exists(file):
            os.remove(file)
        # shutil.rmtree(file)
    return {"ok": 1, 'result_res': result_res}


@app.get('/test')
def run_script():
    str = "测试接口"
    print(f"test============================")
    logging.info("test===============: {}".format(str))
    return str


# @app.post('/api/run/fuzzer')
# def run_fuzz_api(config: FuzzerConfig):
#     logging.info("config: {}".format(str))
#     gptfuzz_v2.run_fuzzer(**config.dict())
#     return "success"

def upload_task_file(output_files):
    if output_files:
        for output_file in output_files:
            file_path = output_file['uploadFileDir']
            bucket_name = output_file['bucketName']
            object_name = output_file['objectName']
            file_name = output_file['fileName']
            if os.path.exists(file_path):
                minio_upload(bucket_name=bucket_name, object_name=object_name, file_name=file_name,
                             save_file_dir=file_path)


def download_task_file(files):
    download_files = []
    for file in files:
        bucket_name = file['bucketName']
        object_name = file['objectName']
        file_name = file['fileName']
        save_file_dir = file['saveFileDir']
        unzip = file['unzip']
        download_file_path = minio_download(bucket_name=bucket_name, object_name=object_name, file_name=file_name,
                                            save_file_dir=save_file_dir, unzip=unzip)
        download_files.append(download_file_path)
    return download_files;


async def run_cmd(cmds, output_files, download_files, task_id):
    try:
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        for cmd_dict in cmds:
            command_list = shlex.split(cmd_dict['cmd'])
            process = await asyncio.create_subprocess_exec(
                *command_list,
                cwd=cmd_dict['directory'],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            print(f"returncode:{process.returncode}")
            if process.returncode == 0:
                print(stdout.decode())
                print(f"stdout:{stderr.decode()}")
            else:
                print(stderr.decode())
        upload_task_file(output_files)
    except asyncio.CancelledError:
        # 取消任务时尝试终止子进程
        process.kill()
        await process.wait()
        print('结束进程')
        raise
    finally:
        # 任务完成后，从字典中移除
        del running_tasks[task_id]
        for file in download_files:
            if os.path.exists(file):
                os.remove(file)


def run_cmd2(cmd):
    print(f'run cmd:{cmd}')
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    result = []
    with process.stdout:
        for line in iter(process.stdout.readline, b''):
            result.append(line.decode().strip())

    print(f'run cmd ====res===stdout ={result}')
    process.wait()
    return result


@app.post("/start_command")
async def start_command(command: Command):
    # print(command)
    logging.info("command: {}".format(command))
    task_id = str(uuid.uuid4())
    download_files = download_task_file(command.download_files)
    task = asyncio.create_task(run_cmd(command.cmd, command.output_files, download_files, task_id))
    running_tasks[task_id] = task
    return {"status": "Command started", "task_id": task_id}


@app.post("/stop_command")
async def stop_command(task_id: str):
    logging.info(f'running_tasks:{running_tasks}')
    # 尝试根据任务 ID 查找任务
    task = running_tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
        # 取消任务
    task.cancel()
    try:
        await task  # 等待任务实际被取消（可选，但可能会捕获异常）
    except asyncio.CancelledError:
        return {"status": "cancelled", "task_id": task_id}
    # 从字典中移除已取消的任务
    # del running_tasks[task_id]
    # running_tasks.pop(task_id)
    return {"status": "Command stopped", "task_id": task_id}


@app.get("/is_command_finished")
async def is_command_finished(task_id: str):
    # 检查任务是否还存在，如果不存在，则认为已完成
    logging.info("task_id: {}".format(task_id))
    if task_id in running_tasks:
        return {"status": "0"}
    else:
        return {"status": "1"}


# 注意：这个接口假设如果任务被取消了，它也会从 running_tasks 中被移除。
# 在 run_command 的 finally 块中，我们确保了无论任务是否成功完成，它都会被移除。
# 如果你想要区分“已完成”和“已取消”的状态，你需要引入额外的状态跟踪机制。
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8091)
