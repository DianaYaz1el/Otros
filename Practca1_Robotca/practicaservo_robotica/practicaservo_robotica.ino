#include <Servo.h>

Servo miServo;

const int pinServo = 9;
int angulo = 0;

void setup() {
  Serial.begin(9600);

  miServo.attach(pinServo);
  miServo.write(0);
}

void loop() {

  if (Serial.available() > 0) {

    angulo = Serial.parseInt();

    while (Serial.available() > 0) {
      Serial.read();
    }

    if (angulo >= 0 && angulo <= 180) {
      miServo.write(angulo);
    }
  }
}