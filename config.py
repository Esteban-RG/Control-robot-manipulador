# Configuración del sistema de control de brazo robótico SCARA

# Configuración de comunicación serial
SERIAL_CONFIG = {
    'port': '/dev/ttyACM0',  # Puerto serial (cambiar según el sistema)
    'baud_rate': 115200,     # Velocidad de comunicación
    'timeout': 1,            # Timeout en segundos
    'encoding': 'utf-8'      # Codificación de caracteres
}

# Configuración de cámaras
CAMERA_CONFIG = {
    'camera_x': {
        'index': 2,          # Índice de la cámara para el eje X
        'resolution': (1580, 1020),
        'fps': 30
    },
    'camera_y': {
        'index': 0,          # Índice de la cámara para el eje Y
        'resolution': (1580, 1020),
        'fps': 30
    }
}

# Configuración de detección de objetos
DETECTION_CONFIG = {
    'min_area': 50,         # Área mínima para detectar objetos
    'confidence_threshold': 0.7,  # Umbral de confianza
    'max_objects': 10        # Máximo número de objetos a detectar
}

# Configuración de colores HSV
COLOR_RANGES = {
    "red": {
        "lower": [0, 100, 100],
        "upper": [10, 255, 255],
        "bgr": (0, 0, 255)
    },
    "red2": {
        "lower": [170, 100, 100],
        "upper": [180, 255, 255],
        "bgr": (0, 0, 255)
    },
    "yellow": {
        "lower": [20, 100, 100],
        "upper": [40, 255, 255],
        "bgr": (0, 255, 255)
    },
    "green": {
        "lower": [50, 100, 100],
        "upper": [80, 255, 255],
        "bgr": (0, 255, 0)
    },
    "blue": {
        "lower": [100, 100, 100],
        "upper": [130, 255, 255],
        "bgr": (255, 0, 0)
    },
    "purple": {
        "lower": [130, 100, 100],
        "upper": [170, 255, 255],
        "bgr": (255, 0, 255)
    },
    "black": {
        "lower": [0, 0, 0],
        "upper": [180, 255, 30],
        "bgr": (0, 0, 0)
    }
}

# Configuración del brazo robótico
ROBOT_CONFIG = {
    'max_speed': 100,        # Velocidad máxima (0-100)
    'acceleration': 50,      # Aceleración (0-100)
    'home_position': [0, 0, 0, 0],  # Posición home [X, Y, Z, Grip]
    'workspace_limits': {
        'x_min': -200, 'x_max': 200,
        'y_min': -200, 'y_max': 200,
        'z_min': 0, 'z_max': 100
    }
}

# Comandos del controlador ESP32
ESP32_COMMANDS = {
    # Movimientos básicos
    'MOVE_X': 'X',           # Mover en eje X
    'MOVE_Y': 'Y',           # Mover en eje Y
    'MOVE_Z': 'Z',           # Mover en eje Z
    'MOVE_GRIP': 'G',        # Mover pinza
    
    # Posiciones predefinidas
    'HOME': 'H',             # Ir a posición home
    'PICK': 'P',             # Posición de recogida
    'PLACE': 'L',            # Posición de colocación
    
    # Control de velocidad
    'SET_SPEED': 'S',        # Establecer velocidad
    'SET_ACCEL': 'A',        # Establecer aceleración
    
    # Estados
    'GET_STATUS': 'T',       # Obtener estado
    'EMERGENCY_STOP': 'E',   # Parada de emergencia
    
    # Rutinas automáticas
    'AUTO_PICK': 'K',        # Recogida automática
    'AUTO_PLACE': 'C',       # Colocación automática
    'VISION_PICK': 'V'       # Recogida por visión
}

# Configuración de la interfaz gráfica
GUI_CONFIG = {
    'window_size': '1200x800',
    'theme': 'clam',
    'button_size': (150, 50),
    'update_rate': 100       # ms entre actualizaciones
}
