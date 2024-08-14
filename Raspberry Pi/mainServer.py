"""
******************************************************************************************
 * FileName      : mainServer.py
 * Description   : Running a web server on Raspberry Pi, communication with ESP32 / React / Arduino Uno / and the model server
 * Author        : GiBeom Park ,  Daeho Kang
 * Last Modified : 2024.08.10
 ******************************************************************************************
"""

import cv2
import requests
import serial
from flask import Flask, jsonify, request, send_file, Response
from datetime import datetime
from PIL import Image
import json
import numpy as np
import base64
import time
import signal
import sys
from flask_cors import CORS
import io
import math

app = Flask(__name__)
CORS(app)

front_server_url = ['http://192.168.137.64:5005/test']
model_server_url = ['http://192.168.137.6:5020/model']
#arduino = serial.Serial('/dev/ttyACM1', 9600)

# 라즈베리에서 인식한 웹캠의 인덱스 ls /dev/video*로 확인 후 수정
camera_array = [0, 2, 4]
# 웹캠 객체를 전역 변수로 선언
webcams = {}
busy = False

def initialize_webcams():
    for index in camera_array:
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            webcams[index] = cap
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            cap.set(cv2.CAP_PROP_FPS, 15)  # FPS 설정
        else:
            print(f"웹캠 {index}을(를) 열 수 없습니다. 다시 시도합니다.")
            cap.release()
            time.sleep(2)  # 잠시 대기 후 다시 시도
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                webcams[index] = cap
                print(f"웹캠 {index}을(를) 성공적으로 열었습니다.")
            else:
                print(f"웹캠 {index}을(를) 여는 데 실패했습니다.")

def release_webcams():
    for cap in webcams.values():
        cap.release()
    print("모든 웹캠을 해제했습니다.")

def capture(n):
    cap = webcams.get(n)
    if cap is None or not cap.isOpened():
        print(f"웹캠 {n}이(가) 열려 있지 않습니다.")
        return None
    if n != 0:
        for _ in range(5):
            cap.read()

    ret, frame = cap.read()
    if not ret:
        print(f"{n}번 프레임을 읽을 수 없습니다. 다시 시도합니다.")
        ret, frame = cap.read()
        if not ret:
            print("프레임을 다시 읽을 수 없습니다.")
            return None
    print(f'{n}번 카메라 성공적으로 찍음')
    return frame

def get_time():
    now = datetime.now()
    return now.isoformat()

recent_sensors_value = {
    'Temperature': 0,
    'humidity': 0,
    'lightLevel': 0,
    'gas': 0,
    'frequencies': [],  # 푸리에 변환된 주파수 데이터를 저장할 리스트
    'fft_magnitude': []  # 푸리에 변환된 크기 데이터를 저장할 리스트
}

@app.route('/camera_on', methods=['GET'])
def camera_on():
    try:
        initialize_webcams()
        return jsonify({'status': 'success', 'message': 'Cameras initialized'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/camera_off', methods=['GET'])
def camera_off():
    try:
        release_webcams()
        return jsonify({'status': 'success', 'message': 'Cameras released.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/')
def show_image():
    return '<h1> welcome </h1>'

@app.route('/monitor/<index>', methods=['GET'])
def show_monitor(index):
    try:
        index = int(index)
        if index not in camera_array:
            return jsonify({'status': 'error', 'message': f'Invalid camera index: {index}'}), 400
        
        ct = capture(index)
        if ct is not None:
            _, img_encoded = cv2.imencode('.jpg', ct)
            return Response(img_encoded.tobytes(), mimetype='image/jpg')
        else:
            return jsonify({'status': 'error', 'message': 'Failed to capture image.'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/sensor', methods=['POST'])
def read_sensor():
    global recent_sensors_value
    if busy:
        print('busy busy')
        return jsonify({})
    
    data = request.get_json()

    # vibrationArray가 존재할 경우 처리
    vibration_array = data.get('vibrationArray', None)
    if vibration_array is not None:
        # 푸리에 변환 수행
        vibration_array = np.array(vibration_array)
        fft_result = np.fft.fft(vibration_array)
        fft_magnitude = np.abs(fft_result)

        # 주파수 축 생성
        sampling_rate = 12000  # 예를 들어 1000Hz로 가정
        frequencies = np.fft.fftfreq(len(vibration_array), d=1/sampling_rate)

        # 양의 주파수 성분만 선택
        positive_freq_indices = frequencies >= 0
        frequencies = frequencies[positive_freq_indices]
        fft_magnitude = fft_magnitude[positive_freq_indices]

        # 변환 결과를 recent_sensors_value에 저장
        recent_sensors_value['frequencies'] = frequencies.tolist()
        recent_sensors_value['fft_magnitude'] = [math.log10(x) if x > 0 else 0 for  x in fft_magnitude.tolist()]
    print(recent_sensors_value)
    # vibrationArray를 제외한 나머지 데이터를 저장
    for key, value in data.items():
        if key != 'vibrationArray':  # vibrationArray는 이미 처리했으므로 제외
            recent_sensors_value[key] = value

    return jsonify(data)

@app.route('/sensor_value', methods=['GET'])
def read_monitor():
    global recent_sensors_value

    return jsonify({
        'Temperature': recent_sensors_value['Temperature'],
        'humidity': recent_sensors_value['humidity'],
        'lightLevel': recent_sensors_value['lightLevel'],
        'gas': recent_sensors_value['gas'],
        'frequencies': recent_sensors_value['frequencies'],
        'fft_magnitude': recent_sensors_value['fft_magnitude']
    })

@app.route('/capture', methods=['POST'])
def read_capture():
    global busy
    busy = True
    try:
        data = request.get_json()
        res = {'status': 'success', 'files': data}
        data2model = {}
        for key in recent_sensors_value.keys():
            data2model[key] = recent_sensors_value[key]
        data2model['time'] = get_time()
        with open('./data.json', 'w') as json_file:
            json.dump(data2model, json_file, indent=4)
        
        image_index = 0
        files = []
        for n in camera_array:
            ct = capture(n)
            if ct is None:
                ct = capture(n)
            if ct is not None:
                _, img_encoded = cv2.imencode('.jpg', ct)
                files.append(('images', (f'image_{image_index}.jpg', img_encoded.tobytes(), 'image/jpg')))
                print(f'camera {n}번  성공적으로 파일에 넣었습니다. ')
            image_index += 1
        
        files.append(('content', ('data.json', json.dumps(data2model), 'application/json')))
        
        response = requests.post(model_server_url[0], files=files)
        print(response)
        busy = False
        return jsonify(res)
    except Exception as e:
        print(f'capture error: {e}')
        busy = False
        return jsonify()

@app.route('/post_processing', methods=['POST'])
def read_post_processing():
    try:
        data = request.get_json()
        print(data)
        if data:
            data2arduino = str(data.get("isNormal", "")).encode('utf-8')
            #arduino.write(data2arduino)
        return jsonify({})
    except Exception as e:
        print(f'post_processing error: {e}')
        return jsonify({})

def signal_handler(sig, frame):
    print('프로그램을 종료합니다.')
    release_webcams()
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)  # SIGINT 신호(Ctrl+C)를 처리하는 핸들러 설정
    try:
        app.run('0.0.0.0', port=5010, debug=True)
    finally:
        release_webcams()
#=========================================================================================
#
# SW_Bootcamp I5
#
#=========================================================================================
