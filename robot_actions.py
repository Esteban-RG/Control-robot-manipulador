class RobotActions:
    def __init__(self, serial_connection):
        self.serial_connection = serial_connection

    def move_up(self):
        """Envía el comando para subir el brazo."""
        self.serial_connection.send_command('A')

    def move_down(self):
        """Envía el comando para bajar el brazo."""
        self.serial_connection.send_command('B')

    def turn_fleft(self):
        """Envía el comando para girar el primer brazo a la izquierda."""
        self.serial_connection.send_command('C')

    def turn_fright(self):
        """Envía el comando para girar el primer brazo a la derecha."""
        self.serial_connection.send_command('D')

    def turn_sleft(self):
        """Envía el comando para girar el segundo brazo a la izquierda."""
        self.serial_connection.send_command('E')

    def turn_sright(self):
        """Envía el comando para girar el segundo brazo a la derecha."""
        self.serial_connection.send_command('F')

    def open_grip(self):
        """Envía el comando para abrir la pinza."""
        self.serial_connection.send_command('E')

    def close_grip(self):
        """Envía el comando para cerrar la pinza."""
        self.serial_connection.send_command('F')