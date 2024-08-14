from ultralytics import YOLO
import os
import cv2
import requests
from PIL import Image
import numpy as np
from flask import Flask, jsonify,render_template, request, send_file
import json
from flask_cors import CORS



# 서버 설정
main_server_url = ['http://52.79.89.88:8002/api/file/battery']
raspberrypi_url = ['http://192.168.137.51:5010/post_processing']
damaged_level = [0.01]
pollution_level =[0.05]
# cut, crop 이미지 크기
size = (224,224)

# 모델 경로 확인
print('load model')
model_path = 'H:/내 드라이브/SF_battery/process/process/Server/Models/best.pt'
if os.path.exists(model_path):
    model = YOLO(model_path)
else:
    print(f"모델 파일을 찾을 수 없습니다: {model_path}")



app = Flask(__name__)
CORS(app) 

# 라즈베리로부터 이미지 업로드 -> 
#                              모델로 이미지 예측
#                             
@app.route('/model', methods=['POST'])
def read_sensor():
    # 업로드 된 이미지 저장
    print("@model")
    print("@model")
    print("@model")
    print("@model")

    # 'content' 필드에서 JSON 데이터 수신
    content_file = request.files.get('content')
    if content_file:
        uploaded_data = json.load(content_file)
    else:
        uploaded_data = {}
    print(uploaded_data)

    # 'images' 필드에서 여러 이미지 파일 수신 및 저장
    images = request.files.getlist('images')
    file_saves = {}
    
    img_list = []
    for image in images:
        # 파일의 저장 경로를 설정합니다.
        file_path = os.path.join('./', image.filename)
        img_list.append(file_path)
        image.save(file_path)
        file_saves[image.filename] = file_path

    print(len(img_list), '장 왔음')

    result_data ={}
    results = model(img_list)
    for i, result in enumerate(results):
        result_data[f'{i}'] = {}
        result_data[f'{i}']['len'] = len(result.boxes.cls.tolist())
        result_data[f'{i}']['cls'] = result.boxes.cls.tolist()
        result_data[f'{i}']['conf'] = result.boxes.conf.tolist()
        result_data[f'{i}']['xyxy'] = result.boxes.xyxy.tolist()
        result.save(filename=f"./result_{i}.jpg")

# 후처리
# 정상/불량 판정
    print(2)
    damaged = 0
    pollution = 0
    battery_exist_list = [1] *len(img_list)
    for i in range(len(img_list)):
        data_part = result_data[f'{i}']
        num = data_part['len']
        cls = data_part['cls']
        conf = data_part['conf']
        xyxy = data_part['xyxy']
        
        if (num == 0) or (0 not in cls):
            battery_exist_list[i] = 0
            continue


        battery = [[],[],[],[]]
        print(3)

        for cl, xy in zip(cls,xyxy):
            damaged_area =0
            pollution_are=0
            if cl ==0:
                battery_exist_list[i] += 1
                battery[0].append(xy[0])
                battery[1].append(xy[1])
                battery[2].append(xy[2])
                battery[3].append(xy[3])
            elif cl ==1:
                damaged_area += (xy[2]-xy[0]) *(xy[3]-xy[1])
            else:
                pollution_are+= (xy[2]-xy[0]) *(xy[3]-xy[1])
        result_data[f'{i}']['filter_battery_xyxy'] = {
            'xmin' : min(battery[0]),
            'ymin' : min(battery[1]),
            'xmax' : max(battery[2]),
            'ymax' : max(battery[3])
        }
        battery_area = (max(battery[2])-min(battery[0])) *(max(battery[3])-min(battery[1]))
        battery_area += 1
        damaged  += damaged_area /battery_area
        pollution+= pollution_are/battery_area

    print(5)
    battery_exist = 1
    for i in battery_exist_list:
        battery_exist*=i

    if battery_exist ==0:
        result_data['result'] = ""
        result_data['isNormal'] = False
    elif damaged> damaged_level[0] and pollution> pollution_level[0]:
        result_data['result'] = "BOTH"
        result_data['isNormal'] = False
    elif damaged<= damaged_level[0] and pollution> pollution_level[0]:
        result_data['result'] = "POLLUTION"
        result_data['isNormal'] = False
    elif damaged> damaged_level[0] and pollution<= pollution_level[0]:
        result_data['result'] = "DAMAGED"
        result_data['isNormal'] = False
    else:
        result_data['result'] = "NORMAL"
        result_data['isNormal'] = True
    
    print("json")

    clsnum2str =[0, 'DAMAGED', 'POLLUTION']

    json_data ={}
    json_data['result']=result_data['result']
    json_data["testDate"] = uploaded_data['time']
    json_data["temperature"] = uploaded_data['Temperature']
    json_data["humidity"] = uploaded_data['humidity']
    json_data["illuminance"] = uploaded_data['lightLevel']
    json_data["damagedLevel"] = round(damaged *100, 1)
    json_data["pollutionLevel"] = round(pollution *100, 1)
    print(1)
    json_data['cameraDefects'] = []
    for i in range(len(img_list)):
        tmp_data = {}
        tmp_data['cameraNumber'] = i
        tmp_data['batteryOutline'] = {}
        tmp_data['defects'] = []
        for cls, xyxy in zip(result_data[f'{i}']['cls'], 
                             result_data[f'{i}']['xyxy']):
            if cls ==0:
                tmp_data['batteryOutline'] ={
                    'xmin' : int(result_data[f'{i}']['filter_battery_xyxy']['xmin']),
                    'ymin' : int(result_data[f'{i}']['filter_battery_xyxy']['ymin']),
                    'xmax' : int(result_data[f'{i}']['filter_battery_xyxy']['xmax']),
                    'ymax' : int(result_data[f'{i}']['filter_battery_xyxy']['ymax'])}

            else:
                tmp_data['defects'].append({
                    'type' : clsnum2str[int(cls)],
                    'xmin' : int(xyxy[0]),
                    'ymin' : int(xyxy[1]),
                    'xmax' : int(xyxy[2]),
                    'ymax' : int(xyxy[3])
                })
        json_data['cameraDefects'].append(tmp_data)
    
    print(json_data)

    files = [
        ('multipartFile', ('image1.jpg', open(f'./result_0.jpg', 'rb'), 'image/jpeg')),
        ('multipartFile', ('image2.jpg', open(f'./result_1.jpg', 'rb'), 'image/jpeg')),
        ('multipartFile', ('image3.jpg', open(f'./result_2.jpg', 'rb'), 'image/jpeg'))
    ]

    print(files)
    files.append(('content', (None, json.dumps(json_data), 'application/json')))
    

    # response = requests.post(main_server_url[0], files=files)
    print('response')


    # RP 서버에 전송
    data2RP = {'isNormal' : result_data['isNormal']}
    response = requests.post(raspberrypi_url[0], json=data2RP)
    print(result_data['isNormal'])
    print('data2RP')


    res = {"i'm fine" : 'thank you'}
    return jsonify(res)




# 요청시 result_img 전송
@app.route('/result_img/<index>', methods=['GET'])
def show_result_img(index):
    print(f'@ result_{index}.jpg')
    image_path = f'./result_{index}.jpg'
    return send_file(image_path, mimetype='image/jpg')



if __name__ == '__main__':
    app.run('0.0.0.0', port=5020, debug=True)