import time
from typing import Optional, Tuple
from serial_communication import SerialConnection
from config import ROBOT_CONFIG

class RobotActions:
    def __init__(self, serial_connection: SerialConnection):
        self.serial_connection = serial_connection
        self.current_position = {'x': 0, 'y': 0, 'z': 0, 'grip': 0}
        self.is_moving = False

    def update_position(self, x: float, y: float, z: float, grip: int = 0):
        """Actualiza la posición actual del brazo."""
        self.current_position = {'x': x, 'y': y, 'z': z, 'grip': grip}

    def get_current_position(self) -> dict:
        """Obtiene la posición actual del brazo."""
        status = self.serial_connection.get_status()
        if status:
            self.update_position(status['x'], status['y'], status['z'], status['grip'])
        return self.current_position

    def move_to_position(self, x: float, y: float, z: float, speed: int = 50) -> bool:
        """Mueve el brazo a una posición específica."""
        # Validar límites del workspace
        limits = ROBOT_CONFIG['workspace_limits']
        x = max(limits['x_min'], min(limits['x_max'], x))
        y = max(limits['y_min'], min(limits['y_max'], y))
        z = max(limits['z_min'], min(limits['z_max'], z))
        
        self.is_moving = True
        success = self.serial_connection.move_to_position(x, y, z, speed)
        if success:
            self.update_position(x, y, z)
        self.is_moving = False
        return success

    def move_relative(self, dx: float, dy: float, dz: float, speed: int = 50) -> bool:
        """Mueve el brazo relativamente desde su posición actual."""
        current = self.get_current_position()
        new_x = current['x'] + dx
        new_y = current['y'] + dy
        new_z = current['z'] + dz
        return self.move_to_position(new_x, new_y, new_z, speed)

    def move_x(self, distance: float, speed: int = 50) -> bool:
        """Mueve el brazo en el eje X."""
        return self.move_relative(distance, 0, 0, speed)

    def move_y(self, distance: float, speed: int = 50) -> bool:
        """Mueve el brazo en el eje Y."""
        return self.move_relative(0, distance, 0, speed)

    def move_z(self, distance: float, speed: int = 50) -> bool:
        """Mueve el brazo en el eje Z."""
        return self.move_relative(0, 0, distance, speed)

    def home_position(self) -> bool:
        """Mueve el brazo a la posición home."""
        home = ROBOT_CONFIG['home_position']
        return self.move_to_position(home[0], home[1], home[2])

    def set_speed(self, speed: int) -> bool:
        """Establece la velocidad del brazo (0-100)."""
        return self.serial_connection.set_speed(speed)

    def set_acceleration(self, acceleration: int) -> bool:
        """Establece la aceleración del brazo (0-100)."""
        acceleration = max(0, min(100, acceleration))
        command = f"A:{acceleration}"
        response = self.serial_connection.send_command(command)
        return response and "OK" in response

    def open_grip(self, position: int = 100) -> bool:
        """Abre la pinza."""
        command = f"G:{position}"
        response = self.serial_connection.send_command(command)
        if response and "OK" in response:
            self.current_position['grip'] = position
        return response and "OK" in response

    def close_grip(self, position: int = 0) -> bool:
        """Cierra la pinza."""
        command = f"G:{position}"
        response = self.serial_connection.send_command(command)
        if response and "OK" in response:
            self.current_position['grip'] = position
        return response and "OK" in response

    def emergency_stop(self) -> bool:
        """Ejecuta parada de emergencia."""
        self.is_moving = False
        return self.serial_connection.emergency_stop()

    def pick_and_place(self, pick_x: float, pick_y: float, place_x: float, place_y: float, z_height: float = 50) -> bool:
        """Ejecuta una secuencia completa de recogida y colocación."""
        print(f"🤖 Iniciando secuencia pick & place...")
        
        # 1. Ir a posición de recogida (arriba)
        if not self.move_to_position(pick_x, pick_y, z_height):
            return False
        
        # 2. Bajar para recoger
        if not self.move_to_position(pick_x, pick_y, 0):
            return False
        
        # 3. Cerrar pinza
        if not self.close_grip():
            return False
        
        # 4. Subir con objeto
        if not self.move_to_position(pick_x, pick_y, z_height):
            return False
        
        # 5. Ir a posición de colocación
        if not self.move_to_position(place_x, place_y, z_height):
            return False
        
        # 6. Bajar para colocar
        if not self.move_to_position(place_x, place_y, 0):
            return False
        
        # 7. Abrir pinza
        if not self.open_grip():
            return False
        
        # 8. Subir sin objeto
        if not self.move_to_position(place_x, place_y, z_height):
            return False
        
        print(f"✅ Secuencia pick & place completada")
        return True

    def auto_pick(self, x: float, y: float) -> bool:
        """Ejecuta rutina automática de recogida."""
        return self.serial_connection.auto_pick(x, y)

    def auto_place(self, x: float, y: float) -> bool:
        """Ejecuta rutina automática de colocación."""
        return self.serial_connection.auto_place(x, y)

    def vision_pick(self, object_id: str) -> bool:
        """Ejecuta recogida basada en visión artificial."""
        return self.serial_connection.vision_pick(object_id)

    def wait_for_movement_complete(self, timeout: float = 30.0) -> bool:
        """Espera a que el movimiento se complete."""
        start_time = time.time()
        while self.is_moving and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        return not self.is_moving

    def get_status(self) -> Optional[dict]:
        """Obtiene el estado completo del brazo."""
        return self.serial_connection.get_status()

    # Métodos de compatibilidad con el código anterior
    def move_up(self):
        """Envía el comando para subir el brazo."""
        self.move_z(10)

    def move_down(self):
        """Envía el comando para bajar el brazo."""
        self.move_z(-10)

    def turn_fleft(self):
        """Envía el comando para girar el primer brazo a la izquierda."""
        self.move_x(-10)

    def turn_fright(self):
        """Envía el comando para girar el primer brazo a la derecha."""
        self.move_x(10)

    def turn_sleft(self):
        """Envía el comando para girar el segundo brazo a la izquierda."""
        self.move_y(-10)

    def turn_sright(self):
        """Envía el comando para girar el segundo brazo a la derecha."""
        self.move_y(10)