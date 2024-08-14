/******************************************************************************************
 * FileName     : main.ino
 * Description  : 온습도 센서, 조도 센서, 가스 센서, 진동센서의 값을 HTTP를 통해 전송 / 온도 28도 초과면 모터(선풍기) 가동
 * Author       : 박기범
 * Created Date : 2024.08.14
 ******************************************************************************************/
#include <WiFi.h>
#include <HTTPClient.h>
#include "dht11.h"
#include "wifi_credentials.h" // WiFi credentials 파일 포함

#define DHT11PIN D3 // DHT11 센서를 연결
#define electric_fan D2 //모터 센서 
const char* postServerName = "http://192.168.137.515010/sensor"; //URL 수정
dht11 DHT11; // 온습도 센서
int light_sensor = A1; // 조도 센서
int gasSensorPin = A3; // MQ-2 센서
int vibration_pin = A4; // 전동 센서

struct SensorData {
  int temperature;
  int humidity;
  int lightLevel;
  int gas;
  int vibrationArray[100]={0}; // 진동 배열을 포함하도록 수정
};

SensorData data; // 전역변수로 센서 데이터 저장

void setup() {
  Serial.begin(9600);
  pinMode(electric_fan,OUTPUT);
  digitalWrite(electric_fan, LOW);
  setupWiFi();
}

void loop() {  
  unsigned long startTime = micros(); // loop 시작 시간 기록
  unsigned long startTime22 = millis(); // loop 시작 시간 기록
  for (int i = 0; i < 100; i++) {
    data.vibrationArray[i] = analogRead(vibration_pin);
    delayMicroseconds(40);  // 샘플링 레이트 조절
  }
  unsigned long endTime1 = micros(); // 종료 시간 측정

  readSensors();

  if(data.temperature>28){
    digitalWrite(electric_fan,HIGH);
  }
  else{
    digitalWrite(electric_fan,LOW);
  }

  String jsonPayload = createJsonPayload(data);
  
  httpPostRequest(postServerName, jsonPayload);
}

void serialPrint(SensorData data){
  // 시리얼 모니터에 출력
  Serial.print("Temperature: ");
  Serial.print(data.temperature); // 온도 값 출력
  Serial.print("℃, Humidity: ");
  Serial.print(data.humidity); // 습도 값 출력
  Serial.print("%, Light Level: ");
  Serial.print(data.lightLevel); // 조도 값 출력
  Serial.print(" lux");
  Serial.print("  gas: ");
  Serial.println(data.gas); // 가스 값 출력
}

//센서 값을 읽고 SensorData 구조체로 반환 
void readSensors() {
  DHT11.read(DHT11PIN); // 온습도 센서(DTH11) 값 측정
  
  data.temperature = DHT11.temperature;
  data.humidity = DHT11.humidity;
  data.lightLevel = analogRead(light_sensor); // 조도 값 측정
  data.gas = analogRead(gasSensorPin);
}

void setupWiFi() {
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void httpPostRequest(const char* serverName, String jsonPayload) {
  HTTPClient http;
  http.begin(serverName);
  http.addHeader("Content-Type", "application/json");
  int httpResponseCode = http.POST(jsonPayload);

  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println(httpResponseCode);
    Serial.println(response);
  } else {
    Serial.print("Error on HTTP request: ");
    Serial.println(httpResponseCode);
  }
  http.end();
}

String createJsonPayload(SensorData data) {

  String jsonPayload = "{";
  jsonPayload += "\"Temperature\":\"" + String(data.temperature) + "\",";
  jsonPayload += "\"humidity\":\"" + String(data.humidity) + "\",";
  jsonPayload += "\"lightLevel\":\"" + String(data.lightLevel) + "\",";
  jsonPayload += "\"gas\":\"" + String(data.gas) + "\",";
  jsonPayload += "\"vibrationArray\":[";
  
  for (int i = 0; i < 100; i++) {
    jsonPayload += String(data.vibrationArray[i]);
    if (i < 99) {
      jsonPayload += ",";
    }
  }
  
  jsonPayload += "]";
  jsonPayload += "}";

  Serial.println("JSON Payload: " + jsonPayload); // 디버그를 위해 JSON 출력
  return jsonPayload;
}

//=========================================================================================
//
// SW_Bootcamp I5
//
//=========================================================================================
