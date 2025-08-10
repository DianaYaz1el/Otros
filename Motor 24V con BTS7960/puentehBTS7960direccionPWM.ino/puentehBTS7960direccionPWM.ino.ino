// ===================================================================
//  Control de Motor 24V con BTS7960 vía Monitor Serie
//  - VERSIÓN CORREGIDA: Mantiene la última velocidad comandada.
//  - Basado en el diagrama de conexión proporcionado.
// ===================================================================

/* ==== Pines (Según tu imagen) ==== */
const uint8_t RPWM_PIN = 3;
const uint8_t LPWM_PIN = 6;
const uint8_t R_EN_PIN = 2;
const uint8_t L_EN_PIN = 5;
const uint8_t R_IS_PIN = 1;
const uint8_t L_IS_PIN = 4;

/* ==== Parámetros de Control ==== */
const int MAX_PWM   = 255;
const int RAMP_STEP = 5;

/* ==== Variables Globales ==== */
int targetVel = 0;
int actualVel = 0;

void setup() {
  Serial.begin(115200);

  pinMode(RPWM_PIN, OUTPUT);
  pinMode(LPWM_PIN, OUTPUT);
  analogWrite(RPWM_PIN, 0);
  analogWrite(LPWM_PIN, 0);

  pinMode(R_EN_PIN, OUTPUT);
  pinMode(L_EN_PIN, OUTPUT);
  digitalWrite(R_EN_PIN, HIGH);
  digitalWrite(L_EN_PIN, HIGH);
  
  pinMode(R_IS_PIN, OUTPUT);
  pinMode(L_IS_PIN, OUTPUT);
  digitalWrite(R_IS_PIN, LOW);
  digitalWrite(L_IS_PIN, LOW);
  
  Serial.println(F("Arduino listo. Esperando comandos... (Versión corregida)"));
}

void rampTowardsTarget() {
  if (actualVel < targetVel) {
    actualVel += RAMP_STEP;
    if (actualVel > targetVel) actualVel = targetVel;
  } else if (actualVel > targetVel) {
    actualVel -= RAMP_STEP;
    if (actualVel < targetVel) actualVel = targetVel;
  }
}

void applyVelocity(int v) {
  v = constrain(v, -MAX_PWM, MAX_PWM);
  
  if (v > 0) {
    analogWrite(LPWM_PIN, 0);
    analogWrite(RPWM_PIN, v);
  } else if (v < 0) {
    analogWrite(RPWM_PIN, 0);
    analogWrite(LPWM_PIN, -v);
  } else {
    analogWrite(RPWM_PIN, 0);
    analogWrite(LPWM_PIN, 0);
  }
}

void loop() {
  // 1. SOLO si hay datos nuevos disponibles...
  if (Serial.available() > 0) {
    // Leemos el nuevo número
    int newCommand = Serial.parseInt();
    
    // ¡Aquí está la magia! Actualizamos la velocidad objetivo.
    // La variable 'targetVel' ahora mantendrá su valor hasta que
    // llegue un nuevo comando válido.
    targetVel = newCommand;
    
    // Imprimimos para confirmar que recibimos el nuevo comando
    Serial.print(F("Nuevo target FIJADO en: "));
    Serial.println(targetVel);
    
    // Limpiamos cualquier carácter extra (como el 'Enter') para
    // evitar lecturas falsas en el siguiente ciclo.
    while(Serial.available() > 0) {
      Serial.read();
    }
  }

  // 2. Mover la velocidad actual hacia el objetivo (rampa)
  rampTowardsTarget();

  // 3. Aplicar la velocidad actual al motor
  applyVelocity(actualVel);

  // 4. Pequeña pausa
  delay(10);
}