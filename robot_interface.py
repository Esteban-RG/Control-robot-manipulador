import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
from PIL import Image, ImageTk
import threading
import time
from typing import Optional

from robot_actions import RobotActions
from robot_routines import RobotRoutines
from vision_system import VisionSystem
from serial_communication import SerialConnection
from config import GUI_CONFIG, CAMERA_CONFIG

class RobotInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Control de Brazo Robótico SCARA")
        self.root.geometry(GUI_CONFIG['window_size'])
        self.root.configure(bg='#2c3e50')
        
        # Variables de control
        self.is_connected = False
        self.vision_enabled = False
        self.current_mode = "manual"  # manual, automatic
        self.update_interval = GUI_CONFIG['update_rate']
        
        # Inicializar componentes
        self.serial_connection = None
        self.robot_actions = None
        self.vision_system = None
        self.robot_routines = None
        
        # Variables de la interfaz
        self.camera_frames = {}
        self.status_labels = {}
        self.position_vars = {}
        
        # Crear interfaz
        self.create_interface()
        
        # Iniciar actualización de estado
        self.update_status()

    def create_interface(self):
        """Crea la interfaz gráfica completa."""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Crear pestañas
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña de control manual
        manual_frame = self.create_manual_control_tab(notebook)
        notebook.add(manual_frame, text="Control Manual")
        
        # Pestaña de control automático
        automatic_frame = self.create_automatic_control_tab(notebook)
        notebook.add(automatic_frame, text="Control Automático")
        
        # Pestaña de visión artificial
        vision_frame = self.create_vision_tab(notebook)
        notebook.add(vision_frame, text="Visión Artificial")
        
        # Pestaña de configuración
        config_frame = self.create_config_tab(notebook)
        notebook.add(config_frame, text="Configuración")
        
        # Barra de estado
        self.create_status_bar(main_frame)

    def create_manual_control_tab(self, parent):
        """Crea la pestaña de control manual."""
        frame = ttk.Frame(parent)
        
        # Frame izquierdo - Control de movimiento
        control_frame = ttk.LabelFrame(frame, text="Control de Movimiento", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Control de posición
        pos_frame = ttk.LabelFrame(control_frame, text="Posición Actual", padding=5)
        pos_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Variables de posición
        self.position_vars = {
            'x': tk.StringVar(value="0.0"),
            'y': tk.StringVar(value="0.0"),
            'z': tk.StringVar(value="0.0"),
            'grip': tk.StringVar(value="0")
        }
        
        # Labels de posición
        ttk.Label(pos_frame, text="X:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(pos_frame, textvariable=self.position_vars['x']).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(pos_frame, text="Y:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(pos_frame, textvariable=self.position_vars['y']).grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(pos_frame, text="Z:").grid(row=2, column=0, sticky=tk.W)
        ttk.Label(pos_frame, textvariable=self.position_vars['z']).grid(row=2, column=1, sticky=tk.W)
        
        ttk.Label(pos_frame, text="Pinza:").grid(row=3, column=0, sticky=tk.W)
        ttk.Label(pos_frame, textvariable=self.position_vars['grip']).grid(row=3, column=1, sticky=tk.W)
        
        # Control de velocidad
        speed_frame = ttk.LabelFrame(control_frame, text="Control de Velocidad", padding=5)
        speed_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.speed_var = tk.IntVar(value=50)
        speed_scale = ttk.Scale(speed_frame, from_=0, to=100, variable=self.speed_var, orient=tk.HORIZONTAL)
        speed_scale.pack(fill=tk.X)
        ttk.Label(speed_frame, textvariable=tk.StringVar(value="Velocidad: 50%")).pack()
        
        # Botones de movimiento
        movement_frame = ttk.LabelFrame(control_frame, text="Movimiento", padding=5)
        movement_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Botones de eje X
        x_frame = ttk.Frame(movement_frame)
        x_frame.pack(fill=tk.X, pady=2)
        ttk.Button(x_frame, text="X-", command=lambda: self.move_relative(-10, 0, 0)).pack(side=tk.LEFT, padx=2)
        ttk.Button(x_frame, text="X+", command=lambda: self.move_relative(10, 0, 0)).pack(side=tk.RIGHT, padx=2)
        ttk.Label(x_frame, text="Eje X").pack(side=tk.TOP)
        
        # Botones de eje Y
        y_frame = ttk.Frame(movement_frame)
        y_frame.pack(fill=tk.X, pady=2)
        ttk.Button(y_frame, text="Y-", command=lambda: self.move_relative(0, -10, 0)).pack(side=tk.LEFT, padx=2)
        ttk.Button(y_frame, text="Y+", command=lambda: self.move_relative(0, 10, 0)).pack(side=tk.RIGHT, padx=2)
        ttk.Label(y_frame, text="Eje Y").pack(side=tk.TOP)
        
        # Botones de eje Z
        z_frame = ttk.Frame(movement_frame)
        z_frame.pack(fill=tk.X, pady=2)
        ttk.Button(z_frame, text="Z-", command=lambda: self.move_relative(0, 0, -10)).pack(side=tk.LEFT, padx=2)
        ttk.Button(z_frame, text="Z+", command=lambda: self.move_relative(0, 0, 10)).pack(side=tk.RIGHT, padx=2)
        ttk.Label(z_frame, text="Eje Z").pack(side=tk.TOP)
        
        # Control de pinza
        grip_frame = ttk.LabelFrame(control_frame, text="Control de Pinza", padding=5)
        grip_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(grip_frame, text="Abrir Pinza", command=self.open_grip).pack(fill=tk.X, pady=2)
        ttk.Button(grip_frame, text="Cerrar Pinza", command=self.close_grip).pack(fill=tk.X, pady=2)
        
        # Botones de acción
        action_frame = ttk.LabelFrame(control_frame, text="Acciones", padding=5)
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="Posición Home", command=self.go_home).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="Parada de Emergencia", command=self.emergency_stop, 
                  style="Emergency.TButton").pack(fill=tk.X, pady=2)
        
        # Frame derecho - Control de posición específica
        position_frame = ttk.LabelFrame(frame, text="Posición Específica", padding=10)
        position_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Entradas de posición
        ttk.Label(position_frame, text="X:").grid(row=0, column=0, sticky=tk.W)
        self.x_entry = ttk.Entry(position_frame)
        self.x_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(position_frame, text="Y:").grid(row=1, column=0, sticky=tk.W)
        self.y_entry = ttk.Entry(position_frame)
        self.y_entry.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(position_frame, text="Z:").grid(row=2, column=0, sticky=tk.W)
        self.z_entry = ttk.Entry(position_frame)
        self.z_entry.grid(row=2, column=1, padx=5, pady=2)
        
        ttk.Button(position_frame, text="Ir a Posición", command=self.go_to_position).grid(row=3, column=0, columnspan=2, pady=10)
        
        return frame

    def create_automatic_control_tab(self, parent):
        """Crea la pestaña de control automático."""
        frame = ttk.Frame(parent)
        
        # Frame izquierdo - Rutinas disponibles
        routines_frame = ttk.LabelFrame(frame, text="Rutinas Automáticas", padding=10)
        routines_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Lista de rutinas
        self.routines_listbox = tk.Listbox(routines_frame, height=10)
        self.routines_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        routines = [
            "square_routine",
            "circle_routine", 
            "pick_and_place_routine",
            "vision_pick_routine",
            "sorting_routine",
            "inspection_routine",
            "calibration_routine"
        ]
        
        for routine in routines:
            self.routines_listbox.insert(tk.END, routine)
        
        # Botones de control de rutinas
        routine_buttons_frame = ttk.Frame(routines_frame)
        routine_buttons_frame.pack(fill=tk.X)
        
        ttk.Button(routine_buttons_frame, text="Ejecutar", command=self.execute_routine).pack(side=tk.LEFT, padx=2)
        ttk.Button(routine_buttons_frame, text="Detener", command=self.stop_routine).pack(side=tk.LEFT, padx=2)
        
        # Frame derecho - Estado de rutinas
        status_frame = ttk.LabelFrame(frame, text="Estado de Rutinas", padding=10)
        status_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Estado actual
        self.routine_status_var = tk.StringVar(value="Sin rutina activa")
        ttk.Label(status_frame, text="Estado:").pack(anchor=tk.W)
        ttk.Label(status_frame, textvariable=self.routine_status_var).pack(anchor=tk.W, pady=(0, 10))
        
        # Log de rutinas
        self.routine_log = tk.Text(status_frame, height=15, width=40)
        self.routine_log.pack(fill=tk.BOTH, expand=True)
        
        return frame

    def create_vision_tab(self, parent):
        """Crea la pestaña de visión artificial."""
        frame = ttk.Frame(parent)
        
        # Frame superior - Control de cámaras
        control_frame = ttk.LabelFrame(frame, text="Control de Cámaras", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(control_frame, text="Iniciar Visión", command=self.start_vision).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Detener Visión", command=self.stop_vision).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Calibrar Cámaras", command=self.calibrate_cameras).pack(side=tk.LEFT, padx=5)
        
        # Frame inferior - Visualización de cámaras
        cameras_frame = ttk.Frame(frame)
        cameras_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cámara X
        camera_x_frame = ttk.LabelFrame(cameras_frame, text="Cámara X", padding=5)
        camera_x_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.camera_x_label = ttk.Label(camera_x_frame, text="Cámara no disponible")
        self.camera_x_label.pack(fill=tk.BOTH, expand=True)
        
        # Cámara Y
        camera_y_frame = ttk.LabelFrame(cameras_frame, text="Cámara Y", padding=5)
        camera_y_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.camera_y_label = ttk.Label(camera_y_frame, text="Cámara no disponible")
        self.camera_y_label.pack(fill=tk.BOTH, expand=True)
        
        return frame

    def create_config_tab(self, parent):
        """Crea la pestaña de configuración."""
        frame = ttk.Frame(parent)
        
        # Configuración de conexión
        connection_frame = ttk.LabelFrame(frame, text="Configuración de Conexión", padding=10)
        connection_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(connection_frame, text="Puerto:").grid(row=0, column=0, sticky=tk.W)
        self.port_var = tk.StringVar(value="/dev/ttyUSB0")
        ttk.Entry(connection_frame, textvariable=self.port_var).grid(row=0, column=1, padx=5)
        
        ttk.Button(connection_frame, text="Conectar", command=self.connect_robot).grid(row=0, column=2, padx=5)
        ttk.Button(connection_frame, text="Desconectar", command=self.disconnect_robot).grid(row=0, column=3, padx=5)
        
        # Estado de conexión
        self.connection_status_var = tk.StringVar(value="Desconectado")
        ttk.Label(connection_frame, text="Estado:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(connection_frame, textvariable=self.connection_status_var).grid(row=1, column=1, sticky=tk.W)
        
        # Configuración de visión
        vision_config_frame = ttk.LabelFrame(frame, text="Configuración de Visión", padding=10)
        vision_config_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(vision_config_frame, text="Guardar Calibración", command=self.save_calibration).pack(side=tk.LEFT, padx=5)
        ttk.Button(vision_config_frame, text="Cargar Calibración", command=self.load_calibration).pack(side=tk.LEFT, padx=5)
        
        return frame

    def create_status_bar(self, parent):
        """Crea la barra de estado."""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Estado de conexión
        self.status_labels['connection'] = ttk.Label(status_frame, text="Desconectado")
        self.status_labels['connection'].pack(side=tk.LEFT, padx=5)
        
        # Estado de visión
        self.status_labels['vision'] = ttk.Label(status_frame, text="Visión: Desactivada")
        self.status_labels['vision'].pack(side=tk.LEFT, padx=5)
        
        # Estado de rutinas
        self.status_labels['routine'] = ttk.Label(status_frame, text="Rutina: Ninguna")
        self.status_labels['routine'].pack(side=tk.LEFT, padx=5)
        
        # Separador
        ttk.Separator(status_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Tiempo de ejecución
        self.status_labels['uptime'] = ttk.Label(status_frame, text="Tiempo: 00:00:00")
        self.status_labels['uptime'].pack(side=tk.RIGHT, padx=5)

    def connect_robot(self):
        """Conecta al robot."""
        try:
            port = self.port_var.get()
            self.serial_connection = SerialConnection(port=port)
            
            if self.serial_connection.open():
                self.robot_actions = RobotActions(self.serial_connection)
                self.robot_routines = RobotRoutines(self.robot_actions)
                self.is_connected = True
                self.connection_status_var.set("Conectado")
                self.status_labels['connection'].config(text="Conectado")
                messagebox.showinfo("Conexión", "Robot conectado exitosamente")
            else:
                messagebox.showerror("Error", "No se pudo conectar al robot")
        except Exception as e:
            messagebox.showerror("Error", f"Error de conexión: {e}")

    def disconnect_robot(self):
        """Desconecta del robot."""
        if self.serial_connection:
            self.serial_connection.close()
            self.is_connected = False
            self.connection_status_var.set("Desconectado")
            self.status_labels['connection'].config(text="Desconectado")
            messagebox.showinfo("Desconexión", "Robot desconectado")

    def start_vision(self):
        """Inicia el sistema de visión."""
        try:
            self.vision_system = VisionSystem()
            self.vision_system.start_detection()
            self.vision_enabled = True
            self.status_labels['vision'].config(text="Visión: Activada")
            messagebox.showinfo("Visión", "Sistema de visión iniciado")
        except Exception as e:
            messagebox.showerror("Error", f"Error al iniciar visión: {e}")

    def stop_vision(self):
        """Detiene el sistema de visión."""
        if self.vision_system:
            self.vision_system.stop_detection()
            self.vision_enabled = False
            self.status_labels['vision'].config(text="Visión: Desactivada")
            messagebox.showinfo("Visión", "Sistema de visión detenido")

    def move_relative(self, dx, dy, dz):
        """Mueve el robot relativamente."""
        if not self.is_connected:
            messagebox.showwarning("Advertencia", "Robot no conectado")
            return
            
        speed = self.speed_var.get()
        self.robot_actions.move_relative(dx, dy, dz, speed)

    def go_to_position(self):
        """Va a una posición específica."""
        if not self.is_connected:
            messagebox.showwarning("Advertencia", "Robot no conectado")
            return
            
        try:
            x = float(self.x_entry.get())
            y = float(self.y_entry.get())
            z = float(self.z_entry.get())
            speed = self.speed_var.get()
            
            self.robot_actions.move_to_position(x, y, z, speed)
        except ValueError:
            messagebox.showerror("Error", "Valores de posición inválidos")

    def go_home(self):
        """Va a la posición home."""
        if not self.is_connected:
            messagebox.showwarning("Advertencia", "Robot no conectado")
            return
            
        self.robot_actions.home_position()

    def open_grip(self):
        """Abre la pinza."""
        if not self.is_connected:
            messagebox.showwarning("Advertencia", "Robot no conectado")
            return
            
        self.robot_actions.open_grip()

    def close_grip(self):
        """Cierra la pinza."""
        if not self.is_connected:
            messagebox.showwarning("Advertencia", "Robot no conectado")
            return
            
        self.robot_actions.close_grip()

    def emergency_stop(self):
        """Parada de emergencia."""
        if self.robot_routines:
            self.robot_routines.emergency_stop()
        messagebox.showwarning("Emergencia", "Parada de emergencia ejecutada")

    def execute_routine(self):
        """Ejecuta la rutina seleccionada."""
        if not self.is_connected:
            messagebox.showwarning("Advertencia", "Robot no conectado")
            return
            
        selection = self.routines_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una rutina")
            return
            
        routine_name = self.routines_listbox.get(selection[0])
        
        # Configurar rutina con visión si está disponible
        if self.vision_system and self.robot_routines:
            self.robot_routines.vision_system = self.vision_system
        
        success = self.robot_routines.start_routine(routine_name)
        if success:
            self.routine_status_var.set(f"Ejecutando: {routine_name}")
            self.status_labels['routine'].config(text=f"Rutina: {routine_name}")

    def stop_routine(self):
        """Detiene la rutina actual."""
        if self.robot_routines:
            self.robot_routines.stop_routine()
            self.routine_status_var.set("Sin rutina activa")
            self.status_labels['routine'].config(text="Rutina: Ninguna")

    def calibrate_cameras(self):
        """Calibra las cámaras."""
        if self.vision_system:
            self.vision_system.calibrate_cameras()
            messagebox.showinfo("Calibración", "Calibración iniciada")

    def save_calibration(self):
        """Guarda la calibración."""
        if self.vision_system:
            filename = filedialog.asksaveasfilename(defaultextension=".npy")
            if filename:
                self.vision_system.save_calibration(filename)

    def load_calibration(self):
        """Carga la calibración."""
        if self.vision_system:
            filename = filedialog.askopenfilename(filetypes=[("NumPy files", "*.npy")])
            if filename:
                self.vision_system.load_calibration(filename)

    def update_status(self):
        """Actualiza el estado de la interfaz."""
        # Actualizar posición si está conectado
        if self.is_connected and self.robot_actions:
            try:
                position = self.robot_actions.get_current_position()
                self.position_vars['x'].set(f"{position['x']:.1f}")
                self.position_vars['y'].set(f"{position['y']:.1f}")
                self.position_vars['z'].set(f"{position['z']:.1f}")
                self.position_vars['grip'].set(str(position['grip']))
            except:
                pass
        
        # Actualizar estado de rutinas
        if self.robot_routines:
            status = self.robot_routines.get_routine_status()
            if status['is_running']:
                self.routine_status_var.set(f"Ejecutando: {status['current_routine']}")
            else:
                self.routine_status_var.set("Sin rutina activa")
        
        # Actualizar tiempo de ejecución
        # (implementar contador de tiempo)
        
        # Programar próxima actualización
        self.root.after(self.update_interval, self.update_status)

    def on_closing(self):
        """Maneja el cierre de la aplicación."""
        if self.vision_system:
            self.stop_vision()
        if self.robot_routines:
            self.stop_routine()
        if self.serial_connection:
            self.disconnect_robot()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = RobotInterface(root)
    
    # Configurar cierre de ventana
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Configurar estilo para botón de emergencia
    style = ttk.Style()
    style.configure("Emergency.TButton", background="red", foreground="white")
    
    root.mainloop()

if __name__ == "__main__":
    main()