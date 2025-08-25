import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
from PIL import Image, ImageTk
import threading
import time
from typing import Optional
import numpy as np

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
        self.camera_images = {}  # Para almacenar las imágenes de tkinter
        
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
        
        # Controles generales
        general_frame = ttk.Frame(control_frame)
        general_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(general_frame, text="Iniciar Visión", command=self.start_vision).pack(side=tk.LEFT, padx=5)
        ttk.Button(general_frame, text="Detener Visión", command=self.stop_vision).pack(side=tk.LEFT, padx=5)
        ttk.Button(general_frame, text="Calibrar Cámaras", command=self.calibrate_cameras).pack(side=tk.LEFT, padx=5)
        ttk.Button(general_frame, text="Probar Cámaras", command=self.test_cameras).pack(side=tk.LEFT, padx=5)
        ttk.Button(general_frame, text="Info Detección", command=self.show_detection_info).pack(side=tk.LEFT, padx=5)
        ttk.Button(general_frame, text="Distancias", command=self.show_square_distances).pack(side=tk.LEFT, padx=5)
        ttk.Button(general_frame, text="Estado Calibración", command=self.show_calibration_status).pack(side=tk.LEFT, padx=5)
        
        # Controles individuales de cámara
        camera_controls_frame = ttk.Frame(control_frame)
        camera_controls_frame.pack(fill=tk.X)
        
        # Control cámara X
        camera_x_control = ttk.LabelFrame(camera_controls_frame, text="Cámara X", padding=5)
        camera_x_control.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.camera_x_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(camera_x_control, text="Activar", variable=self.camera_x_enabled, 
                       command=self.toggle_camera_x).pack(side=tk.LEFT, padx=5)
        
        # Control cámara Y
        camera_y_control = ttk.LabelFrame(camera_controls_frame, text="Cámara Y", padding=5)
        camera_y_control.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        self.camera_y_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(camera_y_control, text="Activar", variable=self.camera_y_enabled, 
                       command=self.toggle_camera_y).pack(side=tk.LEFT, padx=5)
        
        # Frame inferior - Visualización de cámaras
        cameras_frame = ttk.Frame(frame)
        cameras_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cámara X
        camera_x_frame = ttk.LabelFrame(cameras_frame, text="Cámara X", padding=5)
        camera_x_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Crear canvas para la cámara X con mejor configuración
        self.camera_x_canvas = tk.Canvas(camera_x_frame, bg='black', width=320, height=240, 
                                        highlightthickness=1, highlightbackground='gray')
        self.camera_x_canvas.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Cámara Y
        camera_y_frame = ttk.LabelFrame(cameras_frame, text="Cámara Y", padding=5)
        camera_y_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Crear canvas para la cámara Y con mejor configuración
        self.camera_y_canvas = tk.Canvas(camera_y_frame, bg='black', width=320, height=240, 
                                        highlightthickness=1, highlightbackground='gray')
        self.camera_y_canvas.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
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
            # Crear el sistema de visión
            self.vision_system = VisionSystem()
            
            # Intentar iniciar la detección
            if self.vision_system.start_detection():
                self.vision_enabled = True
                self.status_labels['vision'].config(text="Visión: Activada")
                
                # Obtener información sobre cámaras disponibles
                available_cameras = []
                for camera_name, config in CAMERA_CONFIG.items():
                    if self.vision_system.cameras_initialized.get(camera_name, False):
                        available_cameras.append(f"{camera_name} (índice {config['index']})")
                
                if available_cameras:
                    camera_info = f"Cámaras disponibles:\n" + "\n".join(available_cameras) + "\n\nAhora puedes activar las vistas de cámara individualmente."
                    messagebox.showinfo("Visión", f"Sistema de visión iniciado\n{camera_info}")
                else:
                    messagebox.showwarning("Visión", "Sistema de visión iniciado pero no hay cámaras disponibles.")
            else:
                self.vision_enabled = False
                messagebox.showerror("Error", "No se pudo iniciar el sistema de visión. Verifica que las cámaras estén conectadas y disponibles.")
            
        except Exception as e:
            self.vision_enabled = False
            messagebox.showerror("Error", f"Error al iniciar visión: {e}")
            print(f"Error detallado: {e}")

    def stop_vision(self):
        """Detiene el sistema de visión."""
        if self.vision_system:
            self.vision_system.stop_detection()
            self.vision_enabled = False
            self.camera_x_enabled.set(False)
            self.camera_y_enabled.set(False)
            self.status_labels['vision'].config(text="Visión: Desactivada")
            messagebox.showinfo("Visión", "Sistema de visión detenido")

    def toggle_camera_x(self):
        """Activa/desactiva la cámara X."""
        if not self.vision_enabled:
            self.camera_x_enabled.set(False)
            messagebox.showwarning("Advertencia", "Primero inicia el sistema de visión")
            return
            
        if self.camera_x_enabled.get():
            print("✅ Cámara X activada")
        else:
            print("❌ Cámara X desactivada")

    def toggle_camera_y(self):
        """Activa/desactiva la cámara Y."""
        if not self.vision_enabled:
            self.camera_y_enabled.set(False)
            messagebox.showwarning("Advertencia", "Primero inicia el sistema de visión")
            return
            
        if self.camera_y_enabled.get():
            print("✅ Cámara Y activada")
        else:
            print("❌ Cámara Y desactivada")

    def get_canvas_size(self, canvas):
        """Obtiene el tamaño real del canvas."""
        canvas.update()  # Forzar actualización del canvas
        return canvas.winfo_width(), canvas.winfo_height()

    def cv2_to_tkinter(self, cv_image):
        """Convierte una imagen de OpenCV a formato compatible con tkinter."""
        # Convertir de BGR a RGB
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        
        # Obtener dimensiones del canvas (usar tamaño mínimo si no está disponible)
        canvas_width = 520
        canvas_height = 440
        
        # Obtener dimensiones de la imagen original
        height, width = rgb_image.shape[:2]
        
        # Calcular factor de escala para mantener proporción
        scale_x = canvas_width / width
        scale_y = canvas_height / height
        scale = min(scale_x, scale_y)  # Usar el factor más pequeño para mantener proporción
        
        # Calcular nuevas dimensiones
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        # Redimensionar la imagen
        resized_image = cv2.resize(rgb_image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Convertir a PIL Image
        pil_image = Image.fromarray(resized_image)
        
        # Convertir a PhotoImage
        tk_image = ImageTk.PhotoImage(pil_image)
        
        return tk_image, new_width, new_height

    def update_camera_views(self):
        """Actualiza las vistas de las cámaras."""
        if not self.vision_enabled or not self.vision_system:
            # Mostrar mensaje de estado en los canvas
            self.camera_x_canvas.delete("all")
            self.camera_x_canvas.create_text(160, 120, text="Cámara X\nNo disponible", 
                                           fill="white", font=("Arial", 12), anchor=tk.CENTER)
            
            self.camera_y_canvas.delete("all")
            self.camera_y_canvas.create_text(160, 120, text="Cámara Y\nNo disponible", 
                                           fill="white", font=("Arial", 12), anchor=tk.CENTER)
            return
            
        try:
            # Actualizar cámara X si está activada
            if self.camera_x_enabled.get():
                # Usar frame con detecciones y rejilla de coordenadas
                frame_x = self.vision_system.get_frame_with_detections("camera_x")
                if frame_x is not None:
                    # Solo actualizar si hay un frame nuevo
                    if 'camera_x' not in self.camera_images or self.camera_images['camera_x'] is None:
                        tk_image_x, width_x, height_x = self.cv2_to_tkinter(frame_x)
                        self.camera_images['camera_x'] = tk_image_x  # Mantener referencia
                        
                        # Limpiar canvas y mostrar imagen centrada
                        self.camera_x_canvas.delete("all")
                        
                        # Obtener tamaño real del canvas
                        canvas_width, canvas_height = self.get_canvas_size(self.camera_x_canvas)
                        if canvas_width <= 1 or canvas_height <= 1:
                            canvas_width, canvas_height = 320, 240  # Usar tamaño por defecto
                        
                        # Centrar la imagen
                        x_offset = (canvas_width - width_x) // 2
                        y_offset = (canvas_height - height_x) // 2
                        self.camera_x_canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=tk_image_x)
                    else:
                        # Actualizar frame existente
                        tk_image_x, width_x, height_x = self.cv2_to_tkinter(frame_x)
                        self.camera_images['camera_x'] = tk_image_x
                        
                        # Actualizar imagen sin limpiar todo el canvas
                        canvas_width, canvas_height = self.get_canvas_size(self.camera_x_canvas)
                        if canvas_width <= 1 or canvas_height <= 1:
                            canvas_width, canvas_height = 320, 240
                        
                        x_offset = (canvas_width - width_x) // 2
                        y_offset = (canvas_height - height_x) // 2
                        
                        # Actualizar solo la imagen, no todo el canvas
                        self.camera_x_canvas.delete("image_x")
                        self.camera_x_canvas.create_image(x_offset, y_offset, anchor=tk.NW, 
                                                        image=tk_image_x, tags="image_x")
                else:
                    # Mostrar mensaje si no hay frame disponible
                    if 'camera_x' not in self.camera_images or self.camera_images['camera_x'] is not None:
                        self.camera_images['camera_x'] = None
                        self.camera_x_canvas.delete("all")
                        self.camera_x_canvas.create_text(160, 120, text="Cámara X\nSin señal", 
                                                       fill="white", font=("Arial", 12), anchor=tk.CENTER)
            else:
                # Mostrar mensaje de cámara desactivada
                if 'camera_x' not in self.camera_images or self.camera_images['camera_x'] is not None:
                    self.camera_images['camera_x'] = None
                    self.camera_x_canvas.delete("all")
                    self.camera_x_canvas.create_text(160, 120, text="Cámara X\nDesactivada", 
                                                   fill="gray", font=("Arial", 12), anchor=tk.CENTER)
            
            # Actualizar cámara Y si está activada
            if self.camera_y_enabled.get():
                # Usar frame con detecciones y rejilla de coordenadas
                frame_y = self.vision_system.get_frame_with_detections("camera_y")
                if frame_y is not None:
                    # Solo actualizar si hay un frame nuevo
                    if 'camera_y' not in self.camera_images or self.camera_images['camera_y'] is None:
                        tk_image_y, width_y, height_y = self.cv2_to_tkinter(frame_y)
                        self.camera_images['camera_y'] = tk_image_y  # Mantener referencia
                        
                        # Limpiar canvas y mostrar imagen centrada
                        self.camera_y_canvas.delete("all")
                        
                        # Obtener tamaño real del canvas
                        canvas_width, canvas_height = self.get_canvas_size(self.camera_y_canvas)
                        if canvas_width <= 1 or canvas_height <= 1:
                            canvas_width, canvas_height = 320, 240  # Usar tamaño por defecto
                        
                        # Centrar la imagen
                        x_offset = (canvas_width - width_y) // 2
                        y_offset = (canvas_height - height_y) // 2
                        self.camera_y_canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=tk_image_y)
                    else:
                        # Actualizar frame existente
                        tk_image_y, width_y, height_y = self.cv2_to_tkinter(frame_y)
                        self.camera_images['camera_y'] = tk_image_y
                        
                        # Actualizar imagen sin limpiar todo el canvas
                        canvas_width, canvas_height = self.get_canvas_size(self.camera_y_canvas)
                        if canvas_width <= 1 or canvas_height <= 1:
                            canvas_width, canvas_height = 320, 240
                        
                        x_offset = (canvas_width - width_y) // 2
                        y_offset = (canvas_height - height_y) // 2
                        
                        # Actualizar solo la imagen, no todo el canvas
                        self.camera_y_canvas.delete("image_y")
                        self.camera_y_canvas.create_image(x_offset, y_offset, anchor=tk.NW, 
                                                        image=tk_image_y, tags="image_y")
                else:
                    # Mostrar mensaje si no hay frame disponible
                    if 'camera_y' not in self.camera_images or self.camera_images['camera_y'] is not None:
                        self.camera_images['camera_y'] = None
                        self.camera_y_canvas.delete("all")
                        self.camera_y_canvas.create_text(160, 120, text="Cámara Y\nSin señal", 
                                                       fill="white", font=("Arial", 12), anchor=tk.CENTER)
            else:
                # Mostrar mensaje de cámara desactivada
                if 'camera_y' not in self.camera_images or self.camera_images['camera_y'] is not None:
                    self.camera_images['camera_y'] = None
                    self.camera_y_canvas.delete("all")
                    self.camera_y_canvas.create_text(160, 120, text="Cámara Y\nDesactivada", 
                                                   fill="gray", font=("Arial", 12), anchor=tk.CENTER)
                
        except Exception as e:
            print(f"Error al actualizar vistas de cámara: {e}")
            # Mostrar mensaje de error en los canvas
            self.camera_x_canvas.delete("all")
            self.camera_x_canvas.create_text(160, 120, text="Cámara X\nError", 
                                           fill="red", font=("Arial", 12), anchor=tk.CENTER)
            
            self.camera_y_canvas.delete("all")
            self.camera_y_canvas.create_text(160, 120, text="Cámara Y\nError", 
                                           fill="red", font=("Arial", 12), anchor=tk.CENTER)

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
        """Calibra las cámaras usando un objeto de referencia."""
        if not self.vision_enabled or not self.vision_system:
            messagebox.showwarning("Advertencia", "Primero inicia el sistema de visión")
            return
        
        # Crear ventana de diálogo para solicitar medidas de referencia
        dialog = tk.Toplevel(self.root)
        dialog.title("Calibración de Cámaras")
        dialog.geometry("450x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrar la ventana
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text="Calibración con Objeto de Referencia", 
                font=("Arial", 14, "bold")).pack(pady=(0, 15))
        
        # Instrucciones
        instructions = """Mida un objeto de tamaño conocido en la imagen y proporcione:
    - La distancia medida en píxeles
    - El tamaño real del objeto en centímetros

    Ejemplo: Mida un objeto de 10cm que aparece como 150 píxeles en pantalla"""
        ttk.Label(main_frame, text=instructions, wraplength=400, justify=tk.LEFT).pack(pady=(0, 20))
        
        # Frame para entrada de píxeles
        px_frame = ttk.Frame(main_frame)
        px_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(px_frame, text="Distancia en píxeles:", width=20, anchor=tk.W).pack(side=tk.LEFT)
        px_var = tk.StringVar(value="")
        px_entry = ttk.Entry(px_frame, textvariable=px_var, width=15)
        px_entry.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(px_frame, text="px").pack(side=tk.LEFT, padx=(5, 0))
        
        # Frame para entrada de centímetros
        cm_frame = ttk.Frame(main_frame)
        cm_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(cm_frame, text="Distancia real en cm:", width=20, anchor=tk.W).pack(side=tk.LEFT)
        cm_var = tk.StringVar(value="")
        cm_entry = ttk.Entry(cm_frame, textvariable=cm_var, width=15)
        cm_entry.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(cm_frame, text="cm").pack(side=tk.LEFT, padx=(5, 0))

            
        
        # Frame para botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(0, 10))
        
        def perform_calibration():
            try:
                px = float(px_var.get())
                cm = float(cm_var.get())
                if px <= 0 or cm <= 0:
                    messagebox.showerror("Error", "La medida debe ser mayor a 0")
                    return
                
                # Realizar calibración
                self.vision_system.calibrate_with_reference(cm,px)
                
                # Mostrar información de calibración
                calibration_info = f"✅ Sistema calibrado exitosamente\n\n"
                
                for camera_name, factor in self.vision_system.pixels_per_cm.items():
                    calibration_info += f"{camera_name}: {factor:.2f} píxeles/cm\n"
                
                messagebox.showinfo("Calibración Completada", calibration_info)
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Por favor ingresa un número válido para la altura")
        
        def cancel_calibration():
            dialog.destroy()
        
        # Botones
        ttk.Button(button_frame, text="Calibrar", command=perform_calibration).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=cancel_calibration).pack(side=tk.LEFT, padx=5)
        
        # Enfocar en el campo de entrada
        px_entry.focus_set()
        
        # Permitir Enter para confirmar
        dialog.bind('<Return>', lambda e: perform_calibration())
        dialog.bind('<Escape>', lambda e: cancel_calibration())

    def show_calibration_status(self):
        """Muestra el estado actual de calibración del sistema."""
        if not self.vision_enabled or not self.vision_system:
            messagebox.showwarning("Advertencia", "Sistema de visión no activado")
            return
            
        status_info = []
        
        if self.vision_system.is_calibrated:
            status_info.append("✅ SISTEMA CALIBRADO\n")
            status_info.append(f"Altura de la cámara: {self.vision_system.camera_height}cm\n\n")
            
            status_info.append("Factores de conversión por cámara:\n")
            for camera_name, factor in self.vision_system.pixels_per_cm.items():
                status_info.append(f"  • {camera_name}: {factor:.2f} píxeles/cm\n")
            
            status_info.append("\nMedidas mostradas en: CENTÍMETROS")
        else:
            status_info.append("⚠️ SISTEMA NO CALIBRADO\n")
            status_info.append("Para calibrar el sistema:\n")
            status_info.append("1. Presiona 'Calibrar Cámaras'\n")
            status_info.append("2. Ingresa la altura de la cámara\n")
            status_info.append("3. El sistema calculará los factores de conversión\n\n")
            status_info.append("Medidas mostradas en: PÍXELES")
        
        # Mostrar información
        info_text = "Estado de Calibración:" + "".join(status_info)
        messagebox.showinfo("Estado de Calibración", info_text)
        
        # También imprimir en consola
        print("=== ESTADO DE CALIBRACIÓN ===")
        print(info_text)
        print("=============================")

    def show_square_distances(self):
        """Muestra información de las distancias entre cuadrados detectados."""
        if not self.vision_enabled or not self.vision_system:
            messagebox.showwarning("Advertencia", "Sistema de visión no activado")
            return
            
        distance_info = []
        
        # Información de calibración
        if self.vision_system.is_calibrated:
            distance_info.append(f"🎯 Sistema calibrado a {self.vision_system.camera_height}cm de altura\n")
        else:
            distance_info.append("⚠️ Sistema no calibrado - mostrando distancias en píxeles\n")
        
        for camera_name in ['camera_x', 'camera_y']:
            if self.vision_system.cameras_initialized.get(camera_name, False):
                objects = self.vision_system.detected_objects.get(camera_name, [])
                squares = [obj for obj in objects if obj.shape in ["Cuadrado", "Rectangulo"]]
                
                distance_info.append(f"\n{camera_name.upper()}:")
                
                if len(squares) >= 2:
                    distance_info.append(f"  Cuadrados detectados: {len(squares)}")
                    
                    # Calcular todas las distancias
                    for i in range(len(squares)):
                        for j in range(i + 1, len(squares)):
                            square1 = squares[i]
                            square2 = squares[j]
                            
                            # Calcular distancia
                            if self.vision_system.is_calibrated:
                                distance = self.vision_system.calculate_distance_cm(square1.center, square2.center, camera_name)
                                unit = "cm"
                            else:
                                distance = np.sqrt((square2.center[0] - square1.center[0])**2 + 
                                                 (square2.center[1] - square1.center[1])**2)
                                unit = "px"
                            
                            info = f"  • {square1.color} → {square2.color}: {distance:.1f}{unit}"
                            distance_info.append(info)
                elif len(squares) == 1:
                    distance_info.append(f"  Solo 1 cuadrado detectado ({squares[0].color})")
                else:
                    distance_info.append("  No se detectaron cuadrados")
            else:
                distance_info.append(f"\n{camera_name.upper()}: No disponible")
        
        # Mostrar información
        info_text = "Distancias entre cuadrados:" + "".join(distance_info)
        messagebox.showinfo("Distancias entre Cuadrados", info_text)
        
        # También imprimir en consola
        print("=== DISTANCIAS ENTRE CUADRADOS ===")
        print(info_text)
        print("===================================")

    def show_detection_info(self):
        """Muestra información de debug sobre las detecciones actuales."""
        if not self.vision_enabled or not self.vision_system:
            messagebox.showwarning("Advertencia", "Sistema de visión no activado")
            return
            
        detection_info = []
        
        for camera_name in ['camera_x', 'camera_y']:
            if self.vision_system.cameras_initialized.get(camera_name, False):
                objects = self.vision_system.detected_objects.get(camera_name, [])
                detection_info.append(f"\n{camera_name.upper()}:")
                
                if objects:
                    for obj in objects:
                        info = f"  • {obj.color} {obj.shape} en ({obj.center[0]}, {obj.center[1]}) - Conf: {obj.confidence:.2f}"
                        detection_info.append(info)
                else:
                    detection_info.append("  • No se detectaron objetos")
            else:
                detection_info.append(f"\n{camera_name.upper()}: No disponible")
        
        # Mostrar información
        info_text = "Detecciones actuales:" + "".join(detection_info)
        messagebox.showinfo("Información de Detección", info_text)
        
        # También imprimir en consola
        print("=== DETECCIONES ACTUALES ===")
        print(info_text)
        print("=============================")

    def test_cameras(self):
        """Prueba las cámaras individualmente y muestra información de debug."""
        camera_info = []
        
        # Probar todas las cámaras configuradas
        for camera_name, camera_config in CAMERA_CONFIG.items():
            try:
                cap = cv2.VideoCapture(camera_config['index'])
                if cap.isOpened():
                    # Intentar leer un frame
                    ret, frame = cap.read()
                    if ret:
                        height, width = frame.shape[:2]
                        camera_info.append(f"✅ {camera_name}: Índice {camera_config['index']}, Resolución {width}x{height}")
                    else:
                        camera_info.append(f"⚠️ {camera_name}: Índice {camera_config['index']}, No puede leer frames")
                    cap.release()
                else:
                    camera_info.append(f"❌ {camera_name}: Índice {camera_config['index']}, No disponible")
            except Exception as e:
                camera_info.append(f"❌ {camera_name}: Error - {e}")
        
        # Agregar información del estado de la interfaz
        camera_info.append(f"\nEstado de la interfaz:")
        camera_info.append(f"  - Sistema de visión: {'Activado' if self.vision_enabled else 'Desactivado'}")
        camera_info.append(f"  - Cámara X: {'Activada' if self.camera_x_enabled.get() else 'Desactivada'}")
        camera_info.append(f"  - Cámara Y: {'Activada' if self.camera_y_enabled.get() else 'Desactivada'}")
        
        # Agregar información del sistema de visión si está disponible
        if self.vision_system:
            vision_status = self.vision_system.get_status()
            camera_info.append(f"\nEstado del sistema de visión:")
            for camera_name, status in vision_status.items():
                camera_info.append(f"  - {camera_name}:")
                camera_info.append(f"    * Ejecutándose: {'Sí' if status['is_running'] else 'No'}")
                camera_info.append(f"    * Frame disponible: {'Sí' if status['has_frame'] else 'No'}")
                camera_info.append(f"    * Cámara abierta: {'Sí' if status['camera_opened'] else 'No'}")
        
        # Mostrar información en un mensaje
        info_text = "Estado de las cámaras:\n\n" + "\n".join(camera_info)
        messagebox.showinfo("Prueba de Cámaras", info_text)
        
        # También imprimir en consola para debug
        print("=== PRUEBA DE CÁMARAS ===")
        for info in camera_info:
            print(info)
        print("=========================")

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
        
        # Actualizar vistas de cámara
        self.update_camera_views()
        
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