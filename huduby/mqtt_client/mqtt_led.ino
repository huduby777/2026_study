// https://www.hivemq.com/demos/websocket-client/
#include <WiFiS3.h>
#include <ArduinoMqttClient.h>
#include "secret.h"

char ssid[] = SSID;
char pwd[] = PWD;

int status = WL_IDLE_STATUS;

WiFiSSLClient wifiClient;
MqttClient mqttClient(wifiClient);

int port = 8883;
const char broker[] = "broker.hivemq.com";
const char topic[] = "MQTT Test huhuhu";

const int led[3] = {2,3,4};

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);

  while(status != WL_CONNECTED ){
    Serial.println("Attempting to connect to WPA SSID : ");
    Serial.println(ssid);

    status = WiFi.begin(ssid,pwd);
    Serial.println(status);
    delay(50);
  }

  // mqtt 브로커에 연결
  while(!mqttClient.connect(broker,port)){
    Serial.print("MQTT connection failed! ERROR CODE=");
    Serial.println(mqttClient.connectError());
    delay(50);
  }

  Serial.println("MQTT connected!!!"); 
// 메시지를 받았을 때 실행할 수 있는 함수를 등록
  mqttClient.onMessage(onMqttMessage);

  Serial.print("Subscribing to topic:");
  Serial.println(topic);
  Serial.println();

// 이 토픽으로 발행되는 메시지 구독
  mqttClient.subscribe(topic);

  Serial.print("Waiting for messages on topic: ");
  Serial.println(topic);
  Serial.println();

// 버튼의 초기상태 저장
  for (int i = 0; i < 3; i++) {
    pinMode(led[i], OUTPUT);
  }
}

void loop() {
// 수신처리 : 메시지가 도착하면 onMqttMessage() 호출됨
  mqttClient.poll(); 
  delay(500);
}

void onMqttMessage(int messageSize) {
  Serial.println("onMqttMessatage");

// 수신 내용 가져오기  
  String message = mqttClient.readString();
// 수신 토픽
  Serial.print("Received Message : ");
  Serial.println(message);
  Serial.println();

  if( message == "1") {
    digitalWrite(led[0],HIGH);
    digitalWrite(led[1],LOW);
    digitalWrite(led[2],LOW);
    Serial.println("red on");
  } else if ( message == "2") {
    digitalWrite(led[0],LOW);
    digitalWrite(led[1],HIGH);
    digitalWrite(led[2],LOW);
    Serial.println("green on");
  } else if ( message == "3") {
    digitalWrite(led[0],LOW);
    digitalWrite(led[1],LOW);
    digitalWrite(led[2],HIGH);
    Serial.println("blue on");
  }
}