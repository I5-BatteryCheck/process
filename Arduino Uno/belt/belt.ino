#define TRIG 10 //TRIG 핀 설정 (초음파 보내는 핀)
#define ECHO 11 //ECHO 핀 설정 (초음파 받는 핀)

//불량품 제거 인식
#define TRIG_ 6 //6 //TRIG 핀 설정 (초음파 보내는 핀)
#define ECHO_ 7 //7 //ECHO 핀 설정 (초음파 받는 핀)

#define SENSE 12 //12 //제품 감지 LED 등
#define SENSE_ 13 //13 //이동 감지 LED 등

#define CONVEYOR 3

#define outPin 5 // 로봇팔과 연결된 디지털 핀 


bool recived_data = false;
bool defective = false;
bool stopConveyor = false; // 컨베이어 벨트 멈춤 상태를 저장하는 변수

void setup() {
  Serial.begin(9600); //PC모니터로 센서값을 확인하기위해서 시리얼 통신을 정의해줍니다. 
  Serial.setTimeout(10);

  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);

  pinMode(TRIG_, OUTPUT);
  pinMode(ECHO_, INPUT);

  pinMode(SENSE, OUTPUT);
  pinMode(SENSE_, OUTPUT);

  pinMode(CONVEYOR, OUTPUT);
  pinMode(outPin, OUTPUT);
}

void loop() {
  readSerial(); // 시리얼 데이터 먼저 읽기

  long distance = getDistance(TRIG, ECHO);

  if (distance < 10) { // 첫번째 초음파 센서에 제품이 온 경우
    digitalWrite(CONVEYOR, HIGH); // 콘베이어 벨트 멈춤
    digitalWrite(SENSE, HIGH);
    Serial.println("CAPTURE"); // 라즈베리파이에게 시리얼통신으로 보냄
    delay(2000); // 1초 대기
    digitalWrite(CONVEYOR, LOW); // 콘베이어 벨트 작동
    delay(3000); // 1.5초 대기
  }

  long distance_ = getDistance(TRIG_, ECHO_);

  if (distance_ < 10) { // 두번째 초음파 센서에 제품이 온 경우
    if (is_data_received()) { // 시리얼 데이터를 받은 경우
      if (is_defective()) { // 불량품이면 멈춤
        Serial.println("Data Received and stop for 5s and defect remove");

        digitalWrite(CONVEYOR, HIGH); // 불량 제품일 때 벨트를 멈춤

        digitalWrite(outPin, HIGH); // 로봇팔에 신호를 보냄
        delay(1000); // 1초 대기
        digitalWrite(outPin, LOW); // 신호를 끔

        delay(5000); // 5초 정지
        digitalWrite(CONVEYOR, LOW); // 콘베이어 벨트 작동
        delay(2000);
      } else { // 정상이면 지나감
        Serial.println("Data Received and pass");
        digitalWrite(CONVEYOR, LOW); // 콘베이어 벨트 작동
        delay(2000);
      }
    } else { // 시리얼 데이터를 못 받은 경우
      digitalWrite(CONVEYOR, HIGH); // 콘베이어 벨트 대기
    }
  }
}

long getDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);

  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH);
  return duration * 17 / 1000;
}

bool is_data_received() {
  bool tmp = recived_data;
  if (recived_data == true) {
    recived_data = false;
  }
  return tmp;
}

bool is_defective() {
  bool tmp = defective;
  if (defective == true) {
    defective = false;
  }
  return tmp;
}

void readSerial() {
  if (Serial.available() > 0) {
    String incomingData = Serial.readStringUntil('\n'); // 줄 바꿈 문자가 나올 때까지 읽음

    if (incomingData == "Stop") {
      stopConveyor = true; // 컨베이어 벨트 멈춤
    } else if (incomingData == "Start") {
      stopConveyor = false; // 컨베이어 벨트 동작
    } else if (incomingData == "True") {
      recived_data = true;
      defective = false;
    } else if (incomingData == "False") {
      recived_data = true;
      defective = true;
    }
  }
}
