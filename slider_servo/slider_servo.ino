#include <Servo.h>

Servo miServo;
const int pinServo = 9;

void setup() {
  Serial.begin(9600);
  miServo.attach(pinServo);
  miServo.write(90);
}

void loop() {
  if (Serial.available() > 0) {
    int ang = Serial.parseInt();
    while (Serial.available() > 0) Serial.read(); // limpia \n

    if (ang >= 0 && ang <= 180) {
      miServo.write(ang);
      Serial.println(ang);
    }
  }
}
