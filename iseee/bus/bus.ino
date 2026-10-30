#include <WiFiS3.h>
#include <ArduinoJson.h>
#include <LiquidCrystal_I2C.h>

// ===== 설정 =====
const char ssid[] = "모바일핫스팟";
const char pass[] = "12345678";

const char* serviceKey = "d841bc6f1aea6a85cb351cfcbee33669d739879190236561be0e3481f2c415b6";
String stationId = "211000074";      // 시리얼 모니터로 입력해 바꿀 수 있음
const char alarmBus[] = "55";        // 2분 전 알람을 울릴 버스 ("" 이면 알람 끔)

const char server[] = "apis.data.go.kr";
WiFiClient client;

#define BUZZER_PIN 8
LiquidCrystal_I2C lcd(0x27, 16, 2);

const unsigned long apiInterval  = 30000;  // API 갱신 주기
const unsigned long pageInterval = 3000;   // 화면 넘김 주기

// ===== 버스 목록 =====
const int MAX_BUSES = 20;
struct BusInfo {
  char name[10];
  int sec1;   // 첫 번째 버스 남은 초 (-1: 정보 없음)
  int sec2;   // 두 번째 버스 남은 초
};
BusInfo buses[MAX_BUSES];
int busCount = 0;
int pageIdx = 0;
bool fetchOk = false;
bool alarmDone = false;

unsigned long lastApiCall = 0, lastTick = 0, lastPage = 0;
bool needFetch = true;

// ===== 함수 선언 =====
void fetchBusArrivalInfo();
void addBus(JsonObject b);
int  toSec(JsonObject b, const char* secKey, const char* minKey);
void sortBuses();
void updateDisplay();
void checkAlarm();
void triggerBuzzer();
void handleSerial();

void setup() {
  Serial.begin(115200);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Connecting WiFi");

  if (WiFi.status() == WL_NO_MODULE) {
    lcd.clear();
    lcd.print("WiFi Mod Failed");
    while (true);
  }

  int status = WL_IDLE_STATUS;
  while (status != WL_CONNECTED) {
    status = WiFi.begin(ssid, pass);
    delay(3000);
  }

  lcd.clear();
  lcd.print("WiFi Connected!");
  lcd.setCursor(0, 1);
  lcd.print(stationId);
  delay(1500);
  lcd.clear();

  Serial.println("정류장 ID(9자리 숫자)를 입력하면 정류장이 바뀝니다.");
}

void loop() {
  unsigned long now = millis();

  handleSerial();

  // 1) 주기적으로 API 호출 (정류장 변경 시 즉시)
  if (needFetch || now - lastApiCall >= apiInterval) {
    needFetch = false;
    lastApiCall = now;
    fetchBusArrivalInfo();
    updateDisplay();
  }

  // 2) 1초마다 모든 버스의 남은 시간 감소
  if (now - lastTick >= 1000) {
    lastTick = now;
    for (int i = 0; i < busCount; i++) {
      if (buses[i].sec1 > 0) buses[i].sec1--;
      if (buses[i].sec2 > 0) buses[i].sec2--;
    }
    checkAlarm();
    updateDisplay();
  }

  // 3) 3초마다 다음 버스로 화면 넘김
  if (now - lastPage >= pageInterval) {
    lastPage = now;
    if (busCount > 0) pageIdx = (pageIdx + 1) % busCount;
    updateDisplay();
  }
}

// 시리얼로 정류장 ID 입력받기
void handleSerial() {
  if (!Serial.available()) return;
  String s = Serial.readStringUntil('\n');
  s.trim();
  if (s.length() >= 6 && s.length() <= 12) {
    stationId = s;
    busCount = 0;
    pageIdx = 0;
    alarmDone = false;
    needFetch = true;
    lcd.clear();
    lcd.print("Station ID:");
    lcd.setCursor(0, 1);
    lcd.print(stationId);
    Serial.print("정류장 변경: ");
    Serial.println(stationId);
    delay(1000);
    lcd.clear();
  }
}

void fetchBusArrivalInfo() {
  client.stop();
  client.setTimeout(5000);
  fetchOk = false;

  if (!client.connect(server, 80)) return;

  client.print("GET /6410000/busarrivalservice/v2/getBusArrivalListv2");
  client.print("?format=json&serviceKey=");
  client.print(serviceKey);
  client.print("&stationId=");
  client.print(stationId);
  client.print(" HTTP/1.0\r\nHost: ");
  client.print(server);
  client.print("\r\nConnection: close\r\n\r\n");

  unsigned long t = millis();
  while (client.available() == 0) {
    if (millis() - t > 5000) { client.stop(); return; }
  }

  // HTTP 헤더 건너뛰기
  if (!client.find("\r\n\r\n")) { client.stop(); return; }

  // 필요한 필드만 추출
  StaticJsonDocument<512> filter;
  filter["response"]["msgHeader"]["resultCode"] = true;
  JsonObject f = filter["response"]["msgBody"]["busArrivalList"].createNestedObject();
  f["routeName"] = true;
  f["predictTimeSec1"] = true;
  f["predictTime1"] = true;
  f["predictTimeSec2"] = true;
  f["predictTime2"] = true;

  DynamicJsonDocument doc(6144);
  DeserializationError err =
      deserializeJson(doc, client, DeserializationOption::Filter(filter));
  client.stop();

  if (err) {
    Serial.print("JSON 오류: ");
    Serial.println(err.c_str());
    return;
  }

  int resultCode = doc["response"]["msgHeader"]["resultCode"] | -1;
  if (resultCode != 0) {
    Serial.print("API resultCode: ");
    Serial.println(resultCode);
    busCount = 0;
    fetchOk = true;   // 통신은 성공, 버스 정보만 없음
    return;
  }

  busCount = 0;
  JsonVariant list = doc["response"]["msgBody"]["busArrivalList"];
  if (list.is<JsonArray>()) {
    for (JsonObject b : list.as<JsonArray>()) addBus(b);
  } else if (list.is<JsonObject>()) {   // 버스가 1대면 객체로 올 때가 있음
    addBus(list.as<JsonObject>());
  }

  sortBuses();
  if (pageIdx >= busCount) pageIdx = 0;
  fetchOk = true;

  // 디버깅용 출력
  for (int i = 0; i < busCount; i++) {
    Serial.print(buses[i].name);
    Serial.print(" : ");
    Serial.print(buses[i].sec1);
    Serial.print("s / ");
    Serial.print(buses[i].sec2);
    Serial.println("s");
  }
}

void addBus(JsonObject b) {
  if (busCount >= MAX_BUSES) return;
  String rName = b["routeName"].as<String>();
  rName.trim();
  rName.toCharArray(buses[busCount].name, sizeof(buses[busCount].name));
  buses[busCount].sec1 = toSec(b, "predictTimeSec1", "predictTime1");
  buses[busCount].sec2 = toSec(b, "predictTimeSec2", "predictTime2");
  busCount++;
}

// 초 단위 값이 있으면 그것을, 없으면 분 단위 값 x 60을 사용
int toSec(JsonObject b, const char* secKey, const char* minKey) {
  if (!b[secKey].isNull() && b[secKey].as<int>() > 0) return b[secKey].as<int>();
  if (!b[minKey].isNull() && b[minKey].as<int>() > 0) return b[minKey].as<int>() * 60;
  return -1;
}

// 첫 번째 버스 도착이 빠른 순으로 정렬 (정보 없는 버스는 맨 뒤)
void sortBuses() {
  for (int i = 1; i < busCount; i++) {
    BusInfo key = buses[i];
    int j = i - 1;
    while (j >= 0 && ((buses[j].sec1 < 0 && key.sec1 >= 0) ||
                      (key.sec1 >= 0 && buses[j].sec1 > key.sec1))) {
      buses[j + 1] = buses[j];
      j--;
    }
    buses[j + 1] = key;
  }
}

void updateDisplay() {
  char row0[17], row1[17];

  if (!fetchOk) {
    snprintf(row0, sizeof(row0), "%-16s", "Loading / Error");
    snprintf(row1, sizeof(row1), "%-16s", stationId.c_str());
  } else if (busCount == 0) {
    snprintf(row0, sizeof(row0), "%-16s", "No Bus Info");
    snprintf(row1, sizeof(row1), "%-16s", stationId.c_str());
  } else {
    BusInfo &b = buses[pageIdx];

    snprintf(row0, sizeof(row0), "%-8s   %2d/%-2d", b.name, pageIdx + 1, busCount);

    char a[8], n[8];
    if (b.sec1 > 0) snprintf(a, sizeof(a), "%02d:%02d", b.sec1 / 60, b.sec1 % 60);
    else            snprintf(a, sizeof(a), "--:--");
    if (b.sec2 > 0) snprintf(n, sizeof(n), "%dm", b.sec2 / 60);
    else            snprintf(n, sizeof(n), "--");

    snprintf(row1, sizeof(row1), "%-5s Next %-5s", a, n);
  }

  lcd.setCursor(0, 0);
  lcd.print(row0);
  lcd.setCursor(0, 1);
  lcd.print(row1);
}

// 지정한 버스가 2분 이내로 들어오면 알람
void checkAlarm() {
  if (strlen(alarmBus) == 0) return;

  int sec = -1;
  for (int i = 0; i < busCount; i++) {
    if (strcmp(buses[i].name, alarmBus) == 0) { sec = buses[i].sec1; break; }
  }

  if (sec > 150 || sec < 0) {
    alarmDone = false;             // 다음 버스를 위해 재장전
  } else if (sec <= 120 && !alarmDone) {
    triggerBuzzer();
    alarmDone = true;
  }
}

void triggerBuzzer() {
  for (int i = 0; i < 3; i++) {
    tone(BUZZER_PIN, 1500, 150);
    delay(250);
  }
}