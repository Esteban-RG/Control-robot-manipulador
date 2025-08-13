/*
 * Controlador ESP32 para Brazo Robótico SCARA
 * Sistema de control con comunicación serial
 * Compatible con motores paso a paso y servomotores
 */

#include <Arduino.h>
#include <AccelStepper.h>
#include <ESP32Servo.h>

// Configuración de pines
// Motores paso a paso (eje X, Y, Z)
#define STEP_PIN_X 2
#define DIR_PIN_X 3
#define STEP_PIN_Y 4
#define DIR_PIN_Y 5
#define STEP_PIN_Z 6
#define DIR_PIN_Z 7

// Servomotor para pinza
#define SERVO_PIN 8

// Sensores de límite
#define LIMIT_X_MIN 9
#define LIMIT_X_MAX 10
#define LIMIT_Y_MIN 11
#define LIMIT_Y_MAX 12
#define LIMIT_Z_MIN 13
#define LIMIT_Z_MAX 14

// LED de estado
#define STATUS_LED 15

// Configuración de motores
#define STEPS_PER_REV 200
#define MICROSTEPS 16
#define MAX_SPEED 1000
#define ACCELERATION 500

// Variables globales
AccelStepper stepperX(AccelStepper::DRIVER, STEP_PIN_X, DIR_PIN_X);
AccelStepper stepperY(AccelStepper::DRIVER, STEP_PIN_Y, DIR_PIN_Y);
AccelStepper stepperZ(AccelStepper::DRIVER, STEP_PIN_Z, DIR_PIN_Z);
Servo gripperServo;

// Estado del sistema
struct RobotState {
  float x = 0;
  float y = 0;
  float z = 0;
  int grip = 0;
  int speed = 50;
  int acceleration = 50;
  bool is_moving = false;
  bool emergency_stop = false;
} robot_state;

// Variables de control
String inputString = "";
bool stringComplete = false;
unsigned long lastStatusTime = 0;
const unsigned long STATUS_INTERVAL = 1000; // 1 segundo

void setup() {
  // Inicializar comunicación serial
  Serial.begin(115200);
  Serial.println("ESP32 SCARA Robot Controller v1.0");
  
  // Configurar pines de entrada
  pinMode(LIMIT_X_MIN, INPUT_PULLUP);
  pinMode(LIMIT_X_MAX, INPUT_PULLUP);
  pinMode(LIMIT_Y_MIN, INPUT_PULLUP);
  pinMode(LIMIT_Y_MAX, INPUT_PULLUP);
  pinMode(LIMIT_Z_MIN, INPUT_PULLUP);
  pinMode(LIMIT_Z_MAX, INPUT_PULLUP);
  pinMode(STATUS_LED, OUTPUT);
  
  // Configurar motores paso a paso
  setupSteppers();
  
  // Configurar servomotor
  gripperServo.attach(SERVO_PIN);
  gripperServo.write(90); // Posición neutral
  
  // Inicialización
  digitalWrite(STATUS_LED, HIGH);
  delay(1000);
  digitalWrite(STATUS_LED, LOW);
  
  Serial.println("Sistema inicializado");
  Serial.println("Comandos disponibles:");
  Serial.println("X:x,y,z,speed - Mover a posición");
  Serial.println("Y:distance - Mover eje Y");
  Serial.println("Z:distance - Mover eje Z");
  Serial.println("G:position - Control pinza");
  Serial.println("H - Posición home");
  Serial.println("S:speed - Establecer velocidad");
  Serial.println("A:accel - Establecer aceleración");
  Serial.println("T - Obtener estado");
  Serial.println("E - Parada de emergencia");
  Serial.println("K:x,y - Auto pick");
  Serial.println("C:x,y - Auto place");
  Serial.println("V:object_id - Vision pick");
}

void loop() {
  // Procesar comandos seriales
  if (stringComplete) {
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }
  
  // Ejecutar movimientos de motores
  runSteppers();
  
  // Enviar estado periódicamente
  if (millis() - lastStatusTime > STATUS_INTERVAL) {
    sendStatus();
    lastStatusTime = millis();
  }
  
  // Verificar sensores de límite
  checkLimitSwitches();
  
  // Parpadeo del LED de estado
  static unsigned long lastBlink = 0;
  if (millis() - lastBlink > 500) {
    digitalWrite(STATUS_LED, !digitalRead(STATUS_LED));
    lastBlink = millis();
  }
}

void setupSteppers() {
  // Configurar motor X
  stepperX.setMaxSpeed(MAX_SPEED);
  stepperX.setAcceleration(ACCELERATION);
  stepperX.setPinsInverted(false, false, true);
  
  // Configurar motor Y
  stepperY.setMaxSpeed(MAX_SPEED);
  stepperY.setAcceleration(ACCELERATION);
  stepperY.setPinsInverted(false, false, true);
  
  // Configurar motor Z
  stepperZ.setMaxSpeed(MAX_SPEED);
  stepperZ.setAcceleration(ACCELERATION);
  stepperZ.setPinsInverted(false, false, true);
}

void runSteppers() {
  if (!robot_state.emergency_stop) {
    stepperX.run();
    stepperY.run();
    stepperZ.run();
    
    // Actualizar estado de movimiento
    robot_state.is_moving = stepperX.isRunning() || stepperY.isRunning() || stepperZ.isRunning();
  }
}

void processCommand(String command) {
  command.trim();
  
  if (command.length() == 0) return;
  
  char cmd = command.charAt(0);
  String params = command.substring(2); // Saltar "X:" o similar
  
  switch (cmd) {
    case 'X': // Mover a posición específica
      moveToPosition(params);
      break;
      
    case 'Y': // Mover eje Y
      moveY(params.toFloat());
      break;
      
    case 'Z': // Mover eje Z
      moveZ(params.toFloat());
      break;
      
    case 'G': // Control de pinza
      controlGripper(params.toInt());
      break;
      
    case 'H': // Posición home
      goHome();
      break;
      
    case 'S': // Establecer velocidad
      setSpeed(params.toInt());
      break;
      
    case 'A': // Establecer aceleración
      setAcceleration(params.toInt());
      break;
      
    case 'T': // Obtener estado
      sendStatus();
      break;
      
    case 'E': // Parada de emergencia
      emergencyStop();
      break;
      
    case 'K': // Auto pick
      autoPick(params);
      break;
      
    case 'C': // Auto place
      autoPlace(params);
      break;
      
    case 'V': // Vision pick
      visionPick(params);
      break;
      
    default:
      Serial.println("Comando no reconocido: " + command);
      break;
  }
}

void moveToPosition(String params) {
  // Formato: "x,y,z,speed"
  int comma1 = params.indexOf(',');
  int comma2 = params.indexOf(',', comma1 + 1);
  int comma3 = params.indexOf(',', comma2 + 1);
  
  if (comma1 == -1 || comma2 == -1 || comma3 == -1) {
    Serial.println("Error: Formato inválido para movimiento");
    return;
  }
  
  float x = params.substring(0, comma1).toFloat();
  float y = params.substring(comma1 + 1, comma2).toFloat();
  float z = params.substring(comma2 + 1, comma3).toFloat();
  int speed = params.substring(comma3 + 1).toInt();
  
  // Validar límites
  if (x < -200 || x > 200 || y < -200 || y > 200 || z < 0 || z > 100) {
    Serial.println("Error: Posición fuera de límites");
    return;
  }
  
  // Calcular pasos
  long stepsX = mmToSteps(x - robot_state.x);
  long stepsY = mmToSteps(y - robot_state.y);
  long stepsZ = mmToSteps(z - robot_state.z);
  
  // Configurar velocidad
  int motorSpeed = map(speed, 0, 100, 100, MAX_SPEED);
  stepperX.setMaxSpeed(motorSpeed);
  stepperY.setMaxSpeed(motorSpeed);
  stepperZ.setMaxSpeed(motorSpeed);
  
  // Mover motores
  stepperX.move(stepsX);
  stepperY.move(stepsY);
  stepperZ.move(stepsZ);
  
  // Actualizar estado
  robot_state.x = x;
  robot_state.y = y;
  robot_state.z = z;
  robot_state.speed = speed;
  
  Serial.println("OK");
}

void moveY(float distance) {
  long steps = mmToSteps(distance);
  stepperY.move(steps);
  robot_state.y += distance;
  Serial.println("OK");
}

void moveZ(float distance) {
  long steps = mmToSteps(distance);
  stepperZ.move(steps);
  robot_state.z += distance;
  Serial.println("OK");
}

void controlGripper(int position) {
  position = constrain(position, 0, 180);
  gripperServo.write(position);
  robot_state.grip = position;
  Serial.println("OK");
}

void goHome() {
  // Mover a posición home (0, 0, 0)
  moveToPosition("0,0,0,30");
  Serial.println("OK");
}

void setSpeed(int speed) {
  speed = constrain(speed, 0, 100);
  robot_state.speed = speed;
  Serial.println("OK");
}

void setAcceleration(int accel) {
  accel = constrain(accel, 0, 100);
  robot_state.acceleration = accel;
  
  int motorAccel = map(accel, 0, 100, 100, ACCELERATION);
  stepperX.setAcceleration(motorAccel);
  stepperY.setAcceleration(motorAccel);
  stepperZ.setAcceleration(motorAccel);
  
  Serial.println("OK");
}

void emergencyStop() {
  robot_state.emergency_stop = true;
  stepperX.stop();
  stepperY.stop();
  stepperZ.stop();
  stepperX.setCurrentPosition(stepperX.currentPosition());
  stepperY.setCurrentPosition(stepperY.currentPosition());
  stepperZ.setCurrentPosition(stepperZ.currentPosition());
  Serial.println("EMERGENCY_STOP");
}

void autoPick(String params) {
  // Formato: "x,y"
  int comma = params.indexOf(',');
  if (comma == -1) {
    Serial.println("Error: Formato inválido para auto pick");
    return;
  }
  
  float x = params.substring(0, comma).toFloat();
  float y = params.substring(comma + 1).toFloat();
  
  // Secuencia de recogida
  moveToPosition(String(x) + "," + String(y) + ",50,30"); // Ir arriba
  moveToPosition(String(x) + "," + String(y) + ",0,20");   // Bajar
  controlGripper(0);                                       // Cerrar pinza
  moveToPosition(String(x) + "," + String(y) + ",50,30"); // Subir
  
  Serial.println("OK");
}

void autoPlace(String params) {
  // Formato: "x,y"
  int comma = params.indexOf(',');
  if (comma == -1) {
    Serial.println("Error: Formato inválido para auto place");
    return;
  }
  
  float x = params.substring(0, comma).toFloat();
  float y = params.substring(comma + 1).toFloat();
  
  // Secuencia de colocación
  moveToPosition(String(x) + "," + String(y) + ",50,30"); // Ir arriba
  moveToPosition(String(x) + "," + String(y) + ",0,20");   // Bajar
  controlGripper(90);                                      // Abrir pinza
  moveToPosition(String(x) + "," + String(y) + ",50,30"); // Subir
  
  Serial.println("OK");
}

void visionPick(String objectId) {
  // Implementar lógica de recogida por visión
  // Por ahora, simular recogida en posición central
  autoPick("0,0");
  Serial.println("OK");
}

void sendStatus() {
  String status = "STATUS:" + String(robot_state.x, 2) + "," +
                  String(robot_state.y, 2) + "," +
                  String(robot_state.z, 2) + "," +
                  String(robot_state.grip) + "," +
                  String(robot_state.speed);
  Serial.println(status);
}

void checkLimitSwitches() {
  // Verificar sensores de límite
  if (digitalRead(LIMIT_X_MIN) == LOW || digitalRead(LIMIT_X_MAX) == LOW ||
      digitalRead(LIMIT_Y_MIN) == LOW || digitalRead(LIMIT_Y_MAX) == LOW ||
      digitalRead(LIMIT_Z_MIN) == LOW || digitalRead(LIMIT_Z_MAX) == LOW) {
    emergencyStop();
    Serial.println("LIMIT_SWITCH_TRIGGERED");
  }
}

long mmToSteps(float mm) {
  // Convertir milímetros a pasos del motor
  // Ajustar según la configuración mecánica
  return (long)(mm * STEPS_PER_REV * MICROSTEPS / 10.0); // 10mm por revolución
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    if (inChar == '\n') {
      stringComplete = true;
    }
  }
}
