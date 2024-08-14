from ultralytics import YOLO
import os
import io
import cv2
import requests
from PIL import Image
import numpy as np
from flask import Flask, jsonify,render_template, request, send_file
import json
from flask_cors import CORS

from preprocessing import preprocess
from predict import predict
from draw_bb import draw_bb
from make_send_data import make_send_data

# URL
main_server_url = ['http://52.79.89.88:8002/api/file/battery']
raspberrypi_url = ['http://192.168.137.51:5010/post_processing']

# criteria
damaged_criteria = [0.01]
pollution_criteria =[0.05]

# save path
img_path = ['./img_folder']

# Load Model
models = []
# index 0 model is preprocessing model
model_path =[
    './nm_best.pt',
    './bl_best.pt'
]
for path in model_path:
    if os.path.exists(path):
        models.append(YOLO(path))
        print(f"model loaded: {path}")
    else:
        print(f"model NOT FOUND: {path}")


# Flask server
app = Flask(__name__)
CORS(app) 

# Receive Data from Raspberry Pi
# Predict & Send Results
@app.route('/model', methods=['POST'])
def run_model():
    print("@model")
    print("@model")

    # Receive Data from Raspberry Pi
    # Receive sensor data
    content_file = request.files.get('content')
    if content_file:
        uploaded_data = json.load(content_file)
    else:
        uploaded_data = {}
    print(uploaded_data)

    # Receive img data
    images = request.files.getlist('images')
    image_list = []
    for image in images:
        # load img
        img = Image.open(image.stream)
        image_list.append(img)
    print('complete -receice image')

    # Model preprocess (crop image)
    cropped_image_list, crop_point = preprocess(models[0], image_list)
    print('complete -crop image')

    # Model predict
    result = []
    result.append(predict(models[1], cropped_image_list)) # !crop_img_path_list
    print(result)

    # (Not implemented) Ensenble
    if len(result) == 1:
        fine_result = result[0]

    # Draw boundary box
    boxed_image_list = draw_bb(image_list, fine_result, crop_point) #!cropped_image_path_list
    print('complete -boxed image')

    # Post-processing & Make send data
    data2RP, data2MS = make_send_data(uploaded_data, fine_result)
    print('-----------')
    print(data2RP)
    print('-----------')
    print(data2MS)
    print('-----------')

    # Send to mainserver
    files = []

    for i, image in enumerate(boxed_image_list):
        # 이미지 저장을 위한 버퍼 생성
        buf = io.BytesIO()
        image.save(buf, format='JPEG')  # JPEG 형식으로 저장
        img_encoded = buf.getvalue()  # 바이너리 데이터로 변환
        buf.close()  # 버퍼 닫기
        # 이미지 파일 추가
        files.append(('multipartFile', (f'result_img_{i}.jpg', img_encoded, 'image/jpeg')))

    files.append(('content', (None, json.dumps(data2MS), 'application/json')))
    file_names = [file[1][0] for file in files]
    print(file_names)

    response4MS = requests.post(main_server_url[0], files=files)
    print('request mainserver')
    print("Response body (text):")
    print(response4MS.text)  # 문자열 형식의 응답 본문

    #Send to saspberryPi
    response2RP = requests.post(raspberrypi_url[0], json=data2RP)
    print('request raspberryPi')

    # image save
    for i, image in enumerate(image_list):
        image.save(img_path[0]+f'/image_{i}.jpg')
    for i, image in enumerate(cropped_image_list):
        image.save(img_path[0]+f'/cropped_image_{i}.jpg')
    for i, image in enumerate(boxed_image_list):
        image.save(img_path[0]+f'/boxed_image_{i}.jpg')
        
    # Jsonify
    res = {"i'm fine" : 'thank you'}
    return jsonify(res)


# RUN
if __name__ == '__main__':
    app.run('0.0.0.0', port=5020, debug=True)


