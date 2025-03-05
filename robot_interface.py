import tkinter as tk
from tkinter import ttk
from robot_actions import RobotActions
from serial_communication import SerialConnection

class RobotInterface:
    def __init__(self, root, robot_actions):
        self.root = root
        self.robot_actions = robot_actions

        # Configura la ventana
        self.root.title("Control de Robot")
        self.root.geometry("500x400")
        self.root.configure(bg="#f0f0f0")  # Fondo gris claro

        # Estilo para los botones
        self.style = ttk.Style()
        self.style.configure("TButton", 
                            font=("Helvetica", 12), 
                            padding=10, 
                            background="#4CAF50",  # Verde
                            foreground="white")
        self.style.map("TButton", 
                      background=[("active", "#45a049")])  # Verde más oscuro al presionar

        # Botones para las acciones
        self.create_button("Subir Brazo", self.robot_actions.move_up, 0, 0)
        self.create_button("Bajar Brazo", self.robot_actions.move_down, 0, 1)
        self.create_button("Girar Primer Brazo Izquierda", self.robot_actions.turn_fleft, 1, 0)
        self.create_button("Girar Primer Brazo Derecha", self.robot_actions.turn_fright, 1, 1)
        self.create_button("Girar Segundo Brazo Izquierda", self.robot_actions.turn_sleft, 2, 0)
        self.create_button("Girar Segundo Brazo Derecha", self.robot_actions.turn_sright, 2, 1)
        self.create_button("Abrir Pinza", self.robot_actions.open_grip, 3, 0)
        self.create_button("Cerrar Pinza", self.robot_actions.close_grip, 3, 1)

    def create_button(self, text, command, row, column):
        """Crea un botón con estilo moderno."""
        button = ttk.Button(self.root, text=text, style="TButton")
        button.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")

        # Enviar el comando mientras se presiona el botón
        button.bind("<ButtonPress>", lambda event: command())
        button.bind("<ButtonRelease>", lambda event: self.stop_command())

    def stop_command(self):
        """Detiene el envío de comandos."""
        print("Comando detenido")

if __name__ == "__main__":
    # Configura la conexión serial
    serial_conn = SerialConnection(port='/dev/ttyUSB0')  # Cambia al puerto correcto
    serial_conn.open()

    # Crea una instancia de RobotActions
    robot = RobotActions(serial_conn)

    # Crea la interfaz gráfica
    root = tk.Tk()
    app = RobotInterface(root, robot)
    root.mainloop()

    # Cierra la conexión serial al salir
    serial_conn.close()