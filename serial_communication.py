import serial
import time
import threading
from typing import Optional, Callable
from config import SERIAL_CONFIG, ESP32_COMMANDS

class SerialConnection:
    def __init__(self, port: str = None, baud_rate: int = None, timeout: int = None):
        """Inicializa la conexión serial con el ESP32."""
        self.port = port or SERIAL_CONFIG['port']
        self.baud_rate = baud_rate or SERIAL_CONFIG['baud_rate']
        self.timeout = timeout or SERIAL_CONFIG['timeout']
        self.connection: Optional[serial.Serial] = None
        self.is_connected = False
        self.response_callback: Optional[Callable] = None
        self.read_thread: Optional[threading.Thread] = None
        self.stop_reading = False

    def open(self) -> bool:
        """Abre la conexión serial."""
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            self.is_connected = True
            print(f"✅ Conexión establecida en {self.port} a {self.baud_rate} baudios")
            
            # Iniciar thread de lectura
            self.start_reading_thread()
            return True
            
        except Exception as e:
            print(f"❌ Error al abrir la conexión: {e}")
            self.is_connected = False
            return False

    def close(self):
        """Cierra la conexión serial."""
        self.stop_reading = True
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2)
            
        if self.connection and self.connection.is_open:
            self.connection.close()
            self.is_connected = False
            print("🔌 Conexión cerrada.")

    def send_command(self, command: str, wait_response: bool = True, timeout: float = 2.0) -> Optional[str]:
        """Envía un comando al ESP32 y espera respuesta."""
        if not self.is_connected or not self.connection:
            print("❌ Error: La conexión no está abierta.")
            return None

        try:
            # Formato del comando: COMANDO:VALOR\n
            formatted_command = f"{command}\n"
            self.connection.write(formatted_command.encode('utf-8'))
            self.connection.flush()
            print(f"📤 Comando enviado: {command}")

            if wait_response:
                return self.wait_response(timeout)
            return None

        except Exception as e:
            print(f"❌ Error al enviar comando: {e}")
            return None

    def wait_response(self, timeout: float = 2.0) -> Optional[str]:
        """Espera y lee la respuesta del ESP32."""
        start_time = time.time()
        response = ""
        
        while time.time() - start_time < timeout:
            if self.connection.in_waiting:
                line = self.connection.readline().decode('utf-8').strip()
                if line:
                    response = line
                    print(f"📥 Respuesta recibida: {response}")
                    break
            time.sleep(0.01)
        
        return response if response else None

    def start_reading_thread(self):
        """Inicia el thread de lectura continua."""
        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()

    def _read_loop(self):
        """Loop de lectura continua de datos del ESP32."""
        while not self.stop_reading and self.is_connected:
            try:
                if self.connection and self.connection.in_waiting:
                    line = self.connection.readline().decode('utf-8').strip()
                    if line:
                        print(f"📥 Datos recibidos: {line}")
                        if self.response_callback:
                            self.response_callback(line)
                time.sleep(0.01)
            except Exception as e:
                print(f"❌ Error en lectura: {e}")
                break

    def set_response_callback(self, callback: Callable):
        """Establece una función callback para manejar respuestas."""
        self.response_callback = callback

    def move_to_position(self, x: float, y: float, z: float, speed: int = 50) -> bool:
        """Mueve el brazo a una posición específica."""
        command = f"{ESP32_COMMANDS['MOVE_X']}:{x:.2f},{y:.2f},{z:.2f},{speed}"
        response = self.send_command(command)
        return response and "OK" in response

    def set_speed(self, speed: int) -> bool:
        """Establece la velocidad del brazo (0-100)."""
        speed = max(0, min(100, speed))
        command = f"{ESP32_COMMANDS['SET_SPEED']}:{speed}"
        response = self.send_command(command)
        return response and "OK" in response

    def home_position(self) -> bool:
        """Mueve el brazo a la posición home."""
        command = ESP32_COMMANDS['HOME']
        response = self.send_command(command)
        return response and "OK" in response

    def emergency_stop(self) -> bool:
        """Ejecuta parada de emergencia."""
        command = ESP32_COMMANDS['EMERGENCY_STOP']
        response = self.send_command(command, wait_response=False)
        return True

    def get_status(self) -> Optional[dict]:
        """Obtiene el estado actual del brazo."""
        command = ESP32_COMMANDS['GET_STATUS']
        response = self.send_command(command)
        
        if response and "STATUS:" in response:
            try:
                # Parsear respuesta: STATUS:X,Y,Z,GRIP,SPEED
                parts = response.split(":")[1].split(",")
                return {
                    'x': float(parts[0]),
                    'y': float(parts[1]),
                    'z': float(parts[2]),
                    'grip': int(parts[3]),
                    'speed': int(parts[4])
                }
            except:
                pass
        return None

    def auto_pick(self, x: float, y: float) -> bool:
        """Ejecuta rutina automática de recogida."""
        command = f"{ESP32_COMMANDS['AUTO_PICK']}:{x:.2f},{y:.2f}"
        response = self.send_command(command, timeout=10.0)
        return response and "OK" in response

    def auto_place(self, x: float, y: float) -> bool:
        """Ejecuta rutina automática de colocación."""
        command = f"{ESP32_COMMANDS['AUTO_PLACE']}:{x:.2f},{y:.2f}"
        response = self.send_command(command, timeout=10.0)
        return response and "OK" in response

    def vision_pick(self, object_id: str) -> bool:
        """Ejecuta recogida basada en visión artificial."""
        command = f"{ESP32_COMMANDS['VISION_PICK']}:{object_id}"
        response = self.send_command(command, timeout=15.0)
        return response and "OK" in response