#include <ArduinoJson.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd = LiquidCrystal_I2C(0x27,16,2);
void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);

  lcd.init();
  lcd.clear();
  lcd.backlight();
  lcd.setCursor(0,0);

  pinMode(13,OUTPUT);
  pinMode(12,OUTPUT);
  pinMode(11,OUTPUT);

  
  digitalWrite(13,HIGH);
  digitalWrite(12,LOW);
  digitalWrite(11,LOW);
}

String bus_list = "";
void parseBusList(){
  JsonDocument doc;

  DeserializationError error = deserializeJson(doc, bus_list);
  if( error ) {
    Serial.println("Json 파싱 오류");
    Serial.println(error.c_str());
    return;
  }

  JsonArray buses = doc.as<JsonArray>();

  int i = 0;
  for(JsonObject bus : buses) {
    String routeno = bus["routeno"].as<String>();
    int arrtime = bus["arrtime"].as<int>();
    int stationcnt = bus["arrprevstationcnt"].as<int>();
    int minutes = (int)ceil(arrtime / 60.0); 

    String line = "no." + routeno + " " + String(minutes) + "m " + String(stationcnt) + "st";
    lcd.setCursor(0,i++);
    lcd.print(line.substring(0,16));

  }
}
void loop() {
  // put your main code here, to run repeatedly:
  if( Serial.available()){
    bus_list = Serial.readStringUntil('\n');
    if( bus_list.length()) {
      lcd.clear();
      parseBusList();
    }
  }
  delay(500);  
}
