# Sistema de Control de Brazo Robótico SCARA

Sistema completo de control para brazo robótico SCARA con visión artificial, control manual y automático.

## 🚀 Características

- **Control Manual**: Interfaz gráfica para control directo del brazo
- **Control Automático**: Rutinas predefinidas y personalizables
- **Visión Artificial**: Detección de objetos con dos cámaras
- **Comunicación Serial**: Controlador ESP32 integrado
- **Interfaz Moderna**: GUI intuitiva con múltiples pestañas
- **Seguridad**: Parada de emergencia y límites de seguridad

## 📋 Requisitos

### Software
- Python 3.8+
- OpenCV 4.8+
- NumPy
- PySerial
- Tkinter (incluido con Python)

### Hardware
- ESP32
- 3x Motores paso a paso (eje X, Y, Z)
- 1x Servomotor (pinza)
- 6x Sensores de límite
- 2x Cámaras USB
- LED de estado

## 🛠️ Instalación

1. **Clonar el repositorio**:
```bash
git clone <url-del-repositorio>
cd Control-robot-manipulador
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Configurar el ESP32**:
   - Abrir `esp32_controller/esp32_controller.ino` en Arduino IDE
   - Instalar librerías: `AccelStepper`, `Servo`
   - Subir el código al ESP32

4. **Configurar cámaras**:
   - Conectar las dos cámaras USB
   - Verificar índices en `config.py`

## 🎮 Uso

### Iniciar el Sistema

```bash
python main.py
```

O para la interfaz gráfica completa:

```bash
python robot_interface.py
```

### Control Manual

1. **Conectar al robot** en la pestaña "Configuración"
2. **Control de movimiento**:
   - Usar botones X+/X-, Y+/Y-, Z+/Z- para movimiento relativo
   - Ingresar coordenadas específicas para movimiento absoluto
   - Control de velocidad con slider

3. **Control de pinza**:
   - Botones "Abrir Pinza" y "Cerrar Pinza"
   - Posición específica (0-180 grados)

### Control Automático

1. **Rutinas disponibles**:
   - `square_routine`: Dibuja un cuadrado
   - `circle_routine`: Dibuja un círculo
   - `pick_and_place_routine`: Recogida y colocación
   - `vision_pick_routine`: Recogida por visión
   - `sorting_routine`: Clasificación automática
   - `inspection_routine`: Inspección de área
   - `calibration_routine`: Calibración del sistema

2. **Ejecutar rutina**:
   - Seleccionar rutina en la lista
   - Hacer clic en "Ejecutar"
   - Usar "Detener" para interrumpir

### Visión Artificial

1. **Iniciar visión**:
   - Hacer clic en "Iniciar Visión"
   - Las cámaras se activarán automáticamente

2. **Detección de objetos**:
   - Colores: Rojo, Verde, Azul, Amarillo
   - Formas: Círculo, Cuadrado, Triángulo, Pentágono
   - Coordenadas en tiempo real

3. **Calibración**:
   - Usar "Calibrar Cámaras" para ajuste
   - Guardar/cargar calibración

## 🔧 Configuración

### Archivo `config.py`

```python
# Configuración de comunicación serial
SERIAL_CONFIG = {
    'port': '/dev/ttyUSB0',  # Cambiar según el sistema
    'baud_rate': 115200,
    'timeout': 1
}

# Configuración de cámaras
CAMERA_CONFIG = {
    'camera_x': {'index': 0, 'resolution': (640, 480)},
    'camera_y': {'index': 1, 'resolution': (640, 480)}
}

# Límites del workspace
ROBOT_CONFIG = {
    'workspace_limits': {
        'x_min': -200, 'x_max': 200,
        'y_min': -200, 'y_max': 200,
        'z_min': 0, 'z_max': 100
    }
}
```

### ESP32 - Configuración de Pines

```cpp
// Motores paso a paso
#define STEP_PIN_X 2
#define DIR_PIN_X 3
#define STEP_PIN_Y 4
#define DIR_PIN_Y 5
#define STEP_PIN_Z 6
#define DIR_PIN_Z 7

// Servomotor
#define SERVO_PIN 8

// Sensores de límite
#define LIMIT_X_MIN 9
#define LIMIT_X_MAX 10
#define LIMIT_Y_MIN 11
#define LIMIT_Y_MAX 12
#define LIMIT_Z_MIN 13
#define LIMIT_Z_MAX 14
```

## 📁 Estructura del Proyecto

```
Control-robot-manipulador/
├── main.py                 # Punto de entrada principal
├── robot_interface.py      # Interfaz gráfica completa
├── robot_actions.py        # Acciones del robot
├── robot_routines.py       # Rutinas automáticas
├── vision_system.py        # Sistema de visión artificial
├── serial_communication.py # Comunicación serial
├── config.py              # Configuración centralizada
├── artificial_vision.py    # Código original de visión
├── requirements.txt        # Dependencias Python
├── README.md              # Documentación
├── assets/                # Recursos
│   └── interface.png
└── esp32_controller/      # Código del controlador
    └── esp32_controller.ino
```

## 🔌 Comandos del ESP32

| Comando | Descripción | Formato |
|---------|-------------|---------|
| `X` | Mover a posición | `X:x,y,z,speed` |
| `Y` | Mover eje Y | `Y:distance` |
| `Z` | Mover eje Z | `Z:distance` |
| `G` | Control pinza | `G:position` |
| `H` | Posición home | `H` |
| `S` | Establecer velocidad | `S:speed` |
| `A` | Establecer aceleración | `A:accel` |
| `T` | Obtener estado | `T` |
| `E` | Parada de emergencia | `E` |
| `K` | Auto pick | `K:x,y` |
| `C` | Auto place | `C:x,y` |
| `V` | Vision pick | `V:object_id` |

## 🚨 Seguridad

- **Parada de emergencia**: Botón rojo en interfaz
- **Sensores de límite**: Detección automática de límites
- **Validación de coordenadas**: Verificación de workspace
- **Timeouts**: Protección contra comandos colgados

## 🐛 Solución de Problemas

### Error de Conexión Serial
- Verificar puerto correcto en `config.py`
- Comprobar que el ESP32 esté conectado
- Verificar velocidad de baudios (115200)

### Cámaras No Detectadas
- Verificar índices en `config.py`
- Comprobar permisos de acceso a cámaras
- Reiniciar sistema de visión

### Movimientos Imprecisos
- Calibrar sistema de visión
- Verificar configuración de motores
- Ajustar parámetros de velocidad/aceleración

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo LICENSE para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crear una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abrir un Pull Request

## 📞 Soporte

Para soporte técnico o preguntas:
- Crear un issue en GitHub
- Contactar al equipo de desarrollo

---

**Desarrollado con ❤️ para el control de robots SCARA**

