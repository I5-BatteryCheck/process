

#include "dht11.h"

#define DHT11PIN D3 // D2 포트에 DHT11 센서를 연결해야 함
#define LED_PIN D2  // 빨간색 LED 핀 정의

dht11 DHT11; // 온습도 센서
int light_sensor = A1; // 조도센서
int gasSensorPin = A3; // MQ-2 센서의 아날로그 출력 핀
int vibration_pin = A4; // 전동센서 연결

const long sensorInterval = 10; // 센서 값을 10ms마다 읽기

struct SensorData {
  int temperature;
  int humidity;
  int lightLevel;
  int gas;
  int vibrationArray[100] = {0}; // 진동 배열을 포함하도록 수정
};

SensorData data; // 전역변수로 센서 데이터 저장

void setup() {
  Serial.begin(9600);

  // LED 핀 설정
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW); // 초기 상태는 LED 꺼짐

  // 센서 읽기 작업을 비동기로 실행
  xTaskCreatePinnedToCore(
    readSensorsTask,  // 작업 함수
    "SensorTask",     // 작업 이름
    10000,            // 스택 크기
    NULL,             // 작업 함수의 매개변수
    1,                // 우선순위
    NULL,             // 작업 핸들
    0                 // 코어 번호 (0: 코어 0, 1: 코어 1)
  );
}

void loop() {
  // 메인 루프는 비워둡니다. 모든 작업이 비동기로 처리됩니다.
}

void readSensorsTask(void * parameter) {
  while (true) {
    unsigned long startTime = millis(); // loop 시작 시간 기록
    
    for (int i = 0; i < 100; i++) {
      data.vibrationArray[i] = analogRead(vibration_pin);
    }
    
    readSensors2();
    serialPrint(data);

    // 온도에 따라 LED 제어
    if (data.temperature >= 25) {
      digitalWrite(LED_PIN, HIGH); // 온도가 28도 이상일 때 LED 켜기
    } else {
      digitalWrite(LED_PIN, LOW);  // 온도가 28도 이하일 때 LED 끄기
    }

    unsigned long endTime1 = millis(); // 종료 시간 측정
    unsigned long duration = endTime1 - startTime; // 전체 루프 시간
    float sampleRate = 100.0 / (duration / 1000000.0); // 초당 샘플링 횟수 계산
    Serial.print("Loop execution time: ");
    Serial.print(duration); // loop 소요 시간 출력
    Serial.println(" ms");
    Serial.print(sampleRate); // 초당 샘플링 횟수
    Serial.println(" Hz");
    
    vTaskDelay(sensorInterval / portTICK_PERIOD_MS); // 센서 읽기 주기 설정
  }
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

// DHT11 및 조도센서 값을 읽고 SensorData 구조체로 반환하는 함수
void readSensors2() {
  DHT11.read(DHT11PIN); // 온습도 센서(DTH11) 값 측정
  
  data.temperature = DHT11.temperature;
  data.humidity = DHT11.humidity;
  data.lightLevel = analogRead(light_sensor); // 조도 값 측정
  data.gas = analogRead(gasSensorPin);
}
