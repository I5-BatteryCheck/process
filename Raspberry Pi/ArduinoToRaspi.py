"""
******************************************************************************************
 * FileName      : ArduinoToRaspi.py
 * Description   : Serial communication with the connected Arduino Uno board / When the capture signal is sent from the Arduino Uno board, 
                  transmit it to the Raspberry Pi web server
 * Author        : GiBeom Park
 * Last Modified : 2024.08.14
 ******************************************************************************************
"""
import serial
import requests
import json
import time
ser =serial.Serial('/dev/ttyACM1',9600,timeout=1)
url = 'http://192.168.137.62:5010/capture'

while True:
	if ser.in_waiting > 0:
		line=ser.readline().decode('utf-8').strip()
		if line =='CAPTURE':
			print('CAPTURE')
			reponse=requests.post(url)
#=========================================================================================
#
# SW_Bootcamp I5
#
#=========================================================================================
