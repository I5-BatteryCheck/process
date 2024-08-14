/******************************************************************************************
 * FileName     : belt.ino
 * Description  : An Arduino Uno board connected to a belt: When the first ultrasonic sensor detects an object, send a capture signal to the Raspberry Pi. 
                  The belt is controlled based on the battery status determined by the second ultrasonic sensor
 * Author       : GiBeom Park
 * Last Modified : 2024.07.30
 ******************************************************************************************/
//제품 초기 인식
#define TRIG 10 //TRIG 핀 설정 (초음파 보내는 핀)
#define ECHO 11 //ECHO 핀 설정 (초음파 받는 핀)

//불량품 제거 인식
#define TRIG_ 6 //6 //TRIG 핀 설정 (초음파 보내는 핀)
#define ECHO_ 7 //7 //ECHO 핀 설정 (초음파 받는 핀)

#define SENSE 12 //12 //제품 감지 LED 등
#define SENSE_ 13 //13 //이동 감지 LED 등

#define CONVEYOR 3


bool recived_data=false;
bool defective=false;

void setup() {
  Serial.begin(9600); //PC모니터로 센서값을 확인하기위해서 시리얼 통신을 정의해줍니다. 
                       //시리얼 통신을 이용해 PC모니터로 데이터 값을 확인하는 부분은 자주사용되기 때문에
                       //필수로 습득해야하는 교육코스 입니다.
  Serial.setTimeout(10);

  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);

  pinMode(TRIG_, OUTPUT);
  pinMode(ECHO_, INPUT);

  pinMode(SENSE, OUTPUT);
  pinMode(SENSE_, OUTPUT);

  pinMode(CONVEYOR, OUTPUT);

}

void loop() {
  long distance = getDistance(TRIG, ECHO);
  readSerial();

  if (distance<10){ //첫번째 초음파 센서에 배터리 온 경우
    digitalWrite(CONVEYOR, HIGH); //콘베이어벨트 멈춤
    digitalWrite(SENSE, HIGH);
    Serial.print("CAPTURE"); //라즈베리파이에게 시리얼통신으로 보냄
    delay(1000); //1초 대기
    digitalWrite(CONVEYOR, LOW); //콘베이어벨트 작동
  }


  long distance_ = getDistance(TRIG_, ECHO_);

  if(distance_<10){ //첫번째 초음파 센서를 지나 두번째 초음파 센서에 온 경우
    if(is_data_received()){ //시리얼 데이터를 받은 경우
      if(is_defective()){ //불량품이면 멈춤
       Serial.println("Data Received and stop for 5s");
      digitalWrite(CONVEYOR, HIGH);//불량 제품일 때 , 멈춤
      delay(5000); //5초 정지(로봇팔이 움직이는 충분한 속도로 재지정 필요)
      digitalWrite(CONVEYOR, LOW);//콘베이어벨트 작동
      }
      else{
        Serial.println("Data Received and pass");
        digitalWrite(CONVEYOR, LOW);//콘베이어벨트 작동
      }
    }
    else{//시리얼 데이터를 못 받은 경우
      digitalWrite(CONVEYOR, HIGH);//컨베이어 밸트 대기
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


bool is_data_received(){
  bool tmp = recived_data;
  if(recived_data==true){
    recived_data=false;
  }
  return tmp;
}

bool is_defective(){
  bool tmp = defective;
  if(defective==true){
    defective=false;
  }
  return tmp;
}

bool readSerial(){
  if (Serial.available() > 0) {
    // 시리얼 포트에서 한 줄 읽기
    recived_data=true;
    String incomingData = Serial.readStringUntil('\n'); //줄 바꿈 문자가 나올때 까지 읽음
    if(incomingData=="True"){
      defective=true;
    }
    if(incomingData=="False"){
      defective=false;
    }
  }
}
//=========================================================================================
//
// SW_Bootcamp I5
//
//=========================================================================================
