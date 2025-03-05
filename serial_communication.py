import serial

class SerialConnection:
    def __init__(self, port, baud_rate=9600, timeout=1):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.connection = None

    def open(self):
        """Abre la conexión serial."""
        try:
            self.connection = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            print(f"Conexión establecida en {self.port}")
        except Exception as e:
            print(f"Error al abrir la conexión: {e}")

    def close(self):
        """Cierra la conexión serial."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("Conexión cerrada.")

    def send_command(self, command):
        """Envía un comando al Arduino."""
        if self.connection and self.connection.is_open:
            self.connection.write(command.encode())
            print(f"Comando enviado: {command}")
        else:
            print("Error: La conexión no está abierta.")