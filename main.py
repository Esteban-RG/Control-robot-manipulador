#!/usr/bin/env python3
"""
Sistema de Control de Brazo Robótico SCARA
Punto de entrada principal del sistema
"""

import sys
import argparse
from robot_interface import RobotInterface
import tkinter as tk

def main():
    """Función principal del sistema."""
    parser = argparse.ArgumentParser(description='Sistema de Control de Brazo Robótico SCARA')
    parser.add_argument('--gui', action='store_true', help='Iniciar interfaz gráfica')
    parser.add_argument('--port', type=str, default='/dev/ttyUSB0', help='Puerto serial')
    parser.add_argument('--demo', action='store_true', help='Ejecutar demo automático')
    
    args = parser.parse_args()
    
    if args.gui or len(sys.argv) == 1:
        # Iniciar interfaz gráfica
        print("🤖 Iniciando Sistema de Control de Brazo Robótico SCARA")
        print("📱 Cargando interfaz gráfica...")
        
        root = tk.Tk()
        app = RobotInterface(root)
        
        # Configurar cierre de ventana
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        print("✅ Interfaz lista. ¡Bienvenido!")
        root.mainloop()
        
    elif args.demo:
        # Ejecutar demo automático
        print("🎬 Ejecutando demo automático...")
        run_demo(args.port)
        
    else:
        print("❌ Opción no válida. Usa --help para ver opciones disponibles.")

def run_demo(port):
    """Ejecuta una demostración automática del sistema."""
    try:
        from serial_communication import SerialConnection
        from robot_actions import RobotActions
        from robot_routines import RobotRoutines
        from vision_system import VisionSystem
        
        print("🔌 Conectando al robot...")
        serial_conn = SerialConnection(port=port)
        
        if not serial_conn.open():
            print("❌ No se pudo conectar al robot")
            return
            
        robot = RobotActions(serial_conn)
        routines = RobotRoutines(robot)
        
        print("✅ Robot conectado")
        print("🤖 Ejecutando secuencia de demostración...")
        
        # Secuencia de demostración
        print("1️⃣ Moviendo a posición home...")
        robot.home_position()
        
        print("2️⃣ Ejecutando rutina de cuadrado...")
        routines.square_routine(size=30, speed=40)
        
        print("3️⃣ Ejecutando rutina de círculo...")
        routines.circle_routine(radius=20, speed=40)
        
        print("4️⃣ Demostración de pick & place...")
        robot.pick_and_place(20, 20, -20, -20)
        
        print("5️⃣ Volviendo a posición home...")
        robot.home_position()
        
        print("✅ Demostración completada exitosamente!")
        
        # Cerrar conexión
        serial_conn.close()
        
    except Exception as e:
        print(f"❌ Error en demo: {e}")

if __name__ == "__main__":
    main()