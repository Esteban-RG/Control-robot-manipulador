from serial_communication import SerialConnection
from robot_actions import RobotActions
from robot_routines import RobotRoutines

def main():
    # Configura la conexión serial
    serial_conn = SerialConnection(port='/dev/ttyUSB0')  # Cambia 'COM3' por el puerto correcto
    serial_conn.open()

    # Crea una instancia de RobotActions
    robot = RobotActions(serial_conn)

    # Crea una instancia de RobotRoutines
    routines = RobotRoutines(robot)

    # Ejecuta una rutina
    print("Ejecutando rutina: Cuadrado")
    routines.square_routine()

    # Ejecuta otra rutina
    print("Ejecutando rutina: Círculo")
    routines.circle_routine()

    # Cierra la conexión
    serial_conn.close()

if __name__ == "__main__":
    main()