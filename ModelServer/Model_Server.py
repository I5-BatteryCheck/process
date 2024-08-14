from ultralytics import YOLO
import os
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
raspberrypi_url = ['http://192.168.137.62:5010/post_processing']

# criteria
damaged_criteria = [0.01]
pollution_criteria =[0.05]

# save path
img_path = ['./img_folder']

# Load Model
models = []
# index 0 model is preprocessing model
model_path =[
    './best.pt',
    './best.pt'
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
def read_sensor():
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
    img_path_list = []
    for image in images:
        # save img
        file_path = os.path.join(img_path[0], image.filename)
        image.save(file_path)
        img_path_list.append(file_path)
    print(img_path_list)

    # Model preprocess (crop image)
    cropped_image_path_list = preprocess(models[0], img_path_list, img_path[0])
    print(cropped_image_path_list)

    # Model predict
    result = []
    result.append(predict(models[1], img_path_list)) # !crop_img_path_list
    print(result)

    # (Not implemented) Ensenble
    if len(result) == 1:
        fine_result = result[0]

    # Draw boundary box
    boxed_image_path_list = draw_bb(img_path_list, fine_result, img_path[0]) #!cropped_image_path_list
    print(boxed_image_path_list)

    # Post-processing & Make send data
    data2RP, data2MS = make_send_data(uploaded_data, fine_result)
    print(data2RP)
    print(data2MS)

    # Send to mainserver
    files = []
    for i, file_path in enumerate(boxed_image_path_list):
        files.append(('multipartFile', (f'result_img_{i}.jpg', open(file_path, 'rb'), 'image/jpeg')))
    files.append(('content', (None, json.dumps(data2MS), 'application/json')))
    print(files)

    response4MS = requests.post(main_server_url[0], files=files)
    print('Mainserver')
    print("Response body (text):")
    print(response4MS.text)  # 문자열 형식의 응답 본문

    #Send to saspberryPi
    response2RP = requests.post(raspberrypi_url[0], json=data2RP)
    print('RaspberryPi')

    # Jsonify
    res = {"i'm fine" : 'thank you'}
    return jsonify(res)


# RUN
if __name__ == '__main__':
    app.run('0.0.0.0', port=5020, debug=True)


