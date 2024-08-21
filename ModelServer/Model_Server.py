"""
******************************************************************************************
 * FileName      : Model_Server.py
 * Description   : Flask Server for Serving the Model
 * Author        : Dae ho Kang
 * Last modified : 2024.08.14
 ******************************************************************************************
"""


from ultralytics import YOLO
import os
import io
import requests
from PIL import Image
import numpy as np
from flask import Flask, jsonify, request
import json

from predict import predict
from ensemble import ensemble 
from preprocessing import preprocess
from drawBoundarybox import drawBoundarybox
from postprocessing_makeData import postprocessing_makeData

# URL
main_server_url = ['http://52.79.89.88:8002/api/file/battery']
raspberrypi_url = ['http://192.168.137.51:5010/post_processing']

# criteria
criteria = {
    'conf_criteria' : 0.35,
    'damaged_criteria' : 0.01,
    'pollution_criteria' : 0.05
}

# crop pad
pad = {
    'cons_pad' : 0.05,
    'rand_pad' : 0.05
}

# model path
# index 0 model is preprocessing model
model_path =[
    './ModelServer/model_folder/preprocess.pt',
    './ModelServer/model_folder/0.pt',
    './ModelServer/model_folder/1.pt',
    './ModelServer/model_folder/2.pt',
    './ModelServer/model_folder/3.pt',
    './ModelServer/model_folder/4.pt'
]

# save path
img_path = ['../..']


# Load Model
models = []
for path in model_path:
    if os.path.exists(path):
        models.append(YOLO(path))
        print(f"model loaded: {path}")
    else:
        print(f"model NOT FOUND: {path}")


# Flask server
app = Flask(__name__)

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
    cropped_image_list, crop_point = preprocess(models[0], image_list, pad)
    print('complete -crop image')

    # Model predict
    results = []
    for model in models[1:]:
        results.append(predict(model, cropped_image_list, criteria)) 
    #print(results)

    # Ensenble
    if len(results) == 1:
        fine_result = results[0]
    else:
        fine_result = ensemble(results, cropped_image_list)
    print(fine_result)
        

    # Draw boundary box
    boxed_image_list = drawBoundarybox(image_list, fine_result, crop_point)
    print('complete -boxed image')

    # Post-processing & Make send data
    data2RP, data2MS = postprocessing_makeData(uploaded_data, fine_result, criteria)
    print('-----------')
    print(data2RP)
    print('-----------')
    print(data2MS)
    print('-----------')

    # Send to mainserver
    files = []
    for i, image in enumerate(boxed_image_list):
        buf = io.BytesIO() # creat buf to save image
        image.save(buf, format='JPEG')  # save to JPEG
        img_encoded = buf.getvalue()  # transform binary data
        buf.close()
        files.append(('multipartFile', (f'result_img_{i}.jpg', img_encoded, 'image/jpeg')))

    files.append(('content', (None, json.dumps(data2MS), 'application/json')))
    file_names = [file[1][0] for file in files]
    print(file_names)

    response4MS = requests.post(main_server_url[0], files=files)
    print('request mainserver')
    print("Response body (text):") # check request to main server
    print(response4MS.text)

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



#=========================================================================================
#
# SW_Bootcamp I5
#
#=========================================================================================
