import pandas as pd
import json
import websocket
# NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import urllib.request
import urllib.parse
import random
import argparse
import pandas as pd
import time  # 导入 time 模块
from sys import stdout
from tqdm import tqdm
import logging

# 配置日志
logging.basicConfig(filename='generate_clips.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')
logging.info('日志记录开始')
# import json
# from urllib import request, parse
# 定义一个函数来显示GIF图片
def show_gif(fname):
    import base64
    from IPython import display
    with open(fname, 'rb') as fd:
        b64 = base64.b64encode(fd.read()).decode('ascii')
        return display.HTML(f'<img src="data:image/gif;base64,{b64}" />')
# 定义一个函数向服务器队列发送提示信息
def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(
        "http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())
# def queue_prompt(prompt_workflow):
#     p = {"prompt": prompt_workflow}
#     data = json.dumps(p).encode('utf-8')
#     req =  request.Request("http://127.0.0.1:8188/prompt", data=data)
#     request.urlopen(req)
# 定义一个函数来获取图片
def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()
# 定义一个函数来获取历史记录
def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())
# 定义一个函数来获取图片，这涉及到监听WebSocket消息
def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    logging.info('prompt')
    logging.info(prompt)
    logging.info('prompt_id:{}'.format(prompt_id))
    output_images = {}

    max_value = None  # 初始最大值未知
    value = 0  # 初始值
    progress_bar = None

    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break #Execution is done
            elif message['type'] == 'progress':
                data = message['data']

                data = message['data']
                value = data['value']
                max_value = data['max']
                print_progress(data['value'], data['max'])
                # 初始化或更新进度条
                if progress_bar is None or not progress_bar.n:
                    progress_bar = tqdm(total=max_value, desc="Processing", unit="prompt")
                progress_bar.update(value - progress_bar.n)

                # 当进度完成时
                if value == max_value:
                    progress_bar.close()
                    logging.info("\nPrompt complete!")
                # print_progress(data['value'], data['max'])
                # When progress is complete
                # if data['value'] == data['max']:
                #     logging.info("\nPrompt complete!")
        else:
            continue #previews are binary data
        # if isinstance(out, str):
        #     message = json.loads(out)
        #     if message['type'] == 'executing':
        #         data = message['data']
        #         if data['node'] is None and data['prompt_id'] == prompt_id:
        #             logging.info('执行完成')
        #             break   # 执行完成
        # else:
        #     continue  # 预览为二进制数据
    history = get_history(prompt_id)[prompt_id]
    logging.info(history)
    for o in history['outputs']:
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            # 图片分支
            if 'images' in node_output:
                images_output = []
                for image in node_output['images']:
                    image_data = get_image(
                        image['filename'], image['subfolder'], image['type'])
                    images_output.append(image_data)
                output_images[node_id] = images_output
            # 视频分支
            if 'videos' in node_output:
                videos_output = []
                for video in node_output['videos']:
                    video_data = get_image(
                        video['filename'], video['subfolder'], video['type'])
                    videos_output.append(video_data)
                output_images[node_id] = videos_output
    logging.info('获取图片完成')
    # logging.info(output_images)
    return output_images
# 解析工作流并获取图片
def parse_worflow(ws, prompt, seed, workflowfile):
    workflowfile = workflowfile
    logging.info('workflowfile:'+workflowfile)
    with open(workflowfile, 'r', encoding="utf-8") as workflow_api_txt2gif_file:
        prompt_data = json.load(workflow_api_txt2gif_file)

        # give some easy-to-remember names to the nodes
        # chkpoint_loader_node = prompt_data["4"]
        prompt_pos_node = prompt_data["6"]
        # empty_latent_img_node = prompt_data["5"]
        # ksampler_node = prompt_data["3"]
        save_image_node = prompt_data["317"]
        # 设置文本提示
        # prompt_data["6"]["inputs"]["text"] = prompt
#         "320": {
#     "inputs": {
#       "model": "gpt-4o",
#       "user_prompt": "绘本风格 2d, 8 years old chlid girl, short_blond hair,Roxy tries to do some stretching exercises.Though it's a bit strenuous, she doesn't give up."
#     },
#     "class_type": "ChatGPTPrompt",
#     "_meta": {
#       "title": "ChatGPT提示词"
#     }
#   },
# "317": {
#     "inputs": {
#       "filename_prefix": "JourneyPage5",
#       "images": [
#         "231",
#         0
#       ]
#     },
#     "class_type": "SaveImage",
#     "_meta": {
#       "title": "保存图像"
#     }
#   },
        # prompt_data["320"]["inputs"]["user_prompt"] = "绘本风格 2d, 8 years old chlid girl, short_blond hair,"+prompt['Scene']+prompt['Text']
        # +"1 girl walking on campus path, sunset in background, surrounded by trees and flowers"
        prompt_data["6"]["inputs"]["text"] = " black short_hair, bright big eyes, wearing bright colored clothes,"+"wearing bright colored clothes,  "+ prompt['Scene']+prompt['Text'] +", 2d style, the child 8 years old"
        # +prompt['Scene']+prompt['Text']
        logging.info(f"Scene: {prompt['Scene']}===6====\n")
        # logging.info(prompt_data["6"])

        prompt_data["317"]["inputs"]["filename_prefix"] = "Journey"+prompt['PageNumber']
        logging.info(f"PageNumber: {prompt['PageNumber']}===317====\n")
        # logging.info(prompt_data["317"])
        return get_images(ws, prompt_data)
def print_progress(value, max_value):
    bar_length = 50  # Length of the progress bar
    percent = float(value) / max_value
    arrow = '-' * int(round(percent * bar_length) - 1) + '>'
    spaces = ' ' * (bar_length - len(arrow))

    # Update the progress bar in place using stdout instead of print
    stdout.write("\rProgress: [{0}] {1}%".format(arrow + spaces, int(round(percent * 100))))
    stdout.flush()


# 生成图像并显示
def generate_clip(prompt, seed, workflowfile, idx):
    # 这里需要实现生成内容的逻辑

    # prompt['PageNumber'] = prompt['PageNumber'].replace(' ', '').replace('Page', 'Page' + str(idx))

    logging.info(f"PageNumber: {prompt['PageNumber']} Generating clip for prompt: {prompt['Scene']}, seed: {seed}, workflowfile: {workflowfile}, idx: {idx}")
    logging.info('seed:'+str(seed))
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    images = parse_worflow(ws, prompt, seed, workflowfile)
    journey_variable = 'Journey-' + prompt['PageNumber'] + '-' + str(idx)
    logging.info(f"Journey variable: {journey_variable}")
    # logging.info('images:'+str(images))
    for node_id in images:
        for image_data in images[node_id]:
            from datetime import datetime
            # 获取当前时间，并格式化为 YYYYMMDDHHMMSS 的格式
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            # 使用格式化的时间戳在文件名中
            GIF_LOCATION = "{}/{}_{}_{}.png".format(
                SageMaker_ComfyUI, journey_variable, seed, timestamp)
            logging.info('GIF_LOCATION:'+GIF_LOCATION)
            with open(GIF_LOCATION, "wb") as binary_file:
                # 写入二进制文件
                binary_file.write(image_data)
            # show_gif(GIF_LOCATION)
            logging.info("{} DONE!!!".format(GIF_LOCATION))
# Example of reading from a CSV file
# def read_prompts_from_csv(csv_file_path):
#     logging.info('csv_file_path:'+csv_file_path)
#     # df = pd.read_excel(csv_file_path)
#     try:
#         df = pd.read_excel(csv_file_path, engine='openpyxl')
#     except Exception as e:
#         logging.info(f"Error reading the Excel file: {e}")
#         return []
#     return df['Scene'].tolist()
def read_prompts_from_csv(csv_file_path):
    try:
        # 使用 pandas 读取 CSV 文件
        df = pd.read_csv(csv_file_path)
        logging.info(df.columns)
        # if 'Scene' in df.columns:
        #     return df['Scene'].tolist()
        # else:
        #     logging.info("CSV 文件中没有找到 'prompt' 列")
        if 'Scene' in df.columns and 'Text' in df.columns and 'PageNumber' in df.columns:
            return df[['Scene', 'Text', 'PageNumber']].to_dict('records')
        else:
            logging.info("CSV 文件中没有找到所需的列")
        
            return []
    except Exception as e:
        logging.info(f"读取 CSV 文件时出错: {e}")
        return []
def generate_clips(workflowfile, csv_file_path, seed=15465856):
    # 设置工作目录和项目相关的路径
    
    logging.info('csv_file_path:'+csv_file_path)
    prompts = read_prompts_from_csv(csv_file_path)
    if prompts:
        idx = 1
        # for prompt in tqdm(prompts, desc="Initializing", unit="prompt") as t:
        pbar = tqdm(prompts, desc="Initial", unit="prompt")  

        for prompt in pbar:

            prompt['PageNumber'] = prompt['PageNumber'].replace(' ', '') #.replace('Page', 'Page' + str(idx))
            logging.info(prompt)
            if idx == 1:
                generate_clip(prompt, seed, workflowfile, idx)
            # generate_clip(prompt, seed, workflowfile, idx)
            pbar.set_description(f"Processing PageNumber: {prompt['PageNumber']}")
            idx += 1
            time.sleep(1)
# 设置日志  
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')  

COMFYUI_ENDPOINT = '127.0.0.1:8188'  
server_address = COMFYUI_ENDPOINT  
WORKING_DIR = '../output'  
SageMaker_ComfyUI = WORKING_DIR  
client_id = str(uuid.uuid4())  # 这个ID在当前的函数结构中可能未使用  

def main():  
    import argparse  
    import sys  
  
    
  
    parser = argparse.ArgumentParser(description="Generate clips from prompts.")  
    parser.add_argument("workflowfile", type=str, help="Path to the workflow API JSON file.")  
    parser.add_argument("csv_file_path", type=str, help="Path to the CSV file containing prompts.")  
  
    args = parser.parse_args()  
    logging.info(args)  
    generate_clips(args.workflowfile, args.csv_file_path)  
  
if __name__ == "__main__":  
    main()
# if __name__ == "__main__":
#     COMFYUI_ENDPOINT = '127.0.0.1:8188'
#     server_address = COMFYUI_ENDPOINT
#     WORKING_DIR = 'output'
#     SageMaker_ComfyUI = WORKING_DIR
#     client_id = str(uuid.uuid4())  # 生成一个唯一的客户端ID
#     seed = 15465856
#     parser = argparse.ArgumentParser(description="Generate clips from prompts.")
#     parser.add_argument("workflowfile", type=str, help="Path to the workflow API JSON file.")
#     parser.add_argument("csv_file_path", type=str, help="Path to the CSV file containing prompts.")
    
#     args = parser.parse_args()
#     logging.info(args)
#     main(args.workflowfile, args.csv_file_path)       
# Execute the main function
# if __name__ == "__main__":
#     # 设置工作目录和项目相关的路径
#     WORKING_DIR = 'output'
#     SageMaker_ComfyUI = WORKING_DIR
#     workflowfile = 'workflow_api.json'
#     COMFYUI_ENDPOINT = '127.0.0.1:8188'
#     server_address = COMFYUI_ENDPOINT
#     client_id = str(uuid.uuid4())  # 生成一个唯一的客户端ID/
#     seed = 15465856
#     csv_file_path = 'prompt.xlsx'
#     prompts = read_prompts_from_csv(csv_file_path)
#     idx = 1
#     for prompt in prompts:
#         generate_clip(prompt, seed, workflowfile, idx)
#         idx += 1
