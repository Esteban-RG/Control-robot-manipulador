import cv2
import numpy as np
import threading
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from config import CAMERA_CONFIG, COLOR_RANGES, DETECTION_CONFIG

@dataclass
class DetectedObject:
    """Clase para representar un objeto detectado."""
    id: str
    shape: str
    color: str
    center: Tuple[int, int]
    area: float
    confidence: float
    camera: str
    world_coordinates: Optional[Tuple[float, float, float]] = None

class VisionSystem:
    def __init__(self):
        """Inicializa el sistema de visión artificial con múltiples cámaras."""
        self.cameras = {}
        self.detected_objects = {}
        self.is_running = False
        self.calibration_matrix = None
        self.camera_threads = {}
        self.current_frames = {}
        self.frame_locks = {}
        self.cameras_initialized = {}
        
        # Variables de calibración
        self.camera_height = None  # Altura de la cámara en cm
        self.pixels_per_cm = {}    # Factor de conversión píxeles/cm por cámara
        self.is_calibrated = False
        
        # Inicializar cámaras
        self._initialize_cameras()
        
    def _initialize_cameras(self):
        """Inicializa las cámaras configuradas."""
        for camera_name, camera_config in CAMERA_CONFIG.items():
            try:
                cap = cv2.VideoCapture(camera_config['index'])
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_config['resolution'][0])
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_config['resolution'][1])
                    cap.set(cv2.CAP_PROP_FPS, camera_config['fps'])
                    self.cameras[camera_name] = cap
                    self.current_frames[camera_name] = None
                    self.frame_locks[camera_name] = threading.Lock()
                    self.cameras_initialized[camera_name] = True
                    print(f"✅ {camera_name} inicializada correctamente (índice {camera_config['index']})")
                else:
                    print(f"❌ No se pudo abrir {camera_name} (índice {camera_config['index']})")
                    self.cameras_initialized[camera_name] = False
            except Exception as e:
                print(f"❌ Error al inicializar {camera_name}: {e}")
                self.cameras_initialized[camera_name] = False

    def start_detection(self):
        """Inicia la detección continua en todas las cámaras disponibles."""
        if self.is_running:
            print("⚠️ Sistema de visión ya está ejecutándose")
            return True
            
        # Verificar si hay al menos una cámara disponible
        available_cameras = [name for name, initialized in self.cameras_initialized.items() if initialized]
        if not available_cameras:
            print("❌ No hay cámaras disponibles")
            return False
            
        self.is_running = True
        
        # Iniciar threads para cada cámara disponible
        for camera_name in available_cameras:
            thread = threading.Thread(
                target=self._detection_loop,
                args=(camera_name,),
                daemon=True
            )
            self.camera_threads[camera_name] = thread
            thread.start()
            print(f"🔍 Thread iniciado para {camera_name}")
            
        print("🔍 Sistema de visión iniciado")
        return True

    def stop_detection(self):
        """Detiene la detección continua."""
        self.is_running = False
        
        # Esperar a que terminen todos los threads
        for thread in self.camera_threads.values():
            thread.join(timeout=2)
            
        # Liberar todas las cámaras
        for cap in self.cameras.values():
            if cap:
                cap.release()
            
        print("🛑 Sistema de visión detenido")

    def _detection_loop(self, camera_name: str):
        """Loop de detección para una cámara específica."""
        cap = self.cameras[camera_name]
        
        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                continue
                
            # Guardar frame actual para esta cámara
            with self.frame_locks[camera_name]:
                self.current_frames[camera_name] = frame.copy()
                
            # Detectar objetos en el frame
            objects = self._detect_objects_in_frame(frame, camera_name)
            
            # Actualizar objetos detectados para esta cámara
            self.detected_objects[camera_name] = objects
            
            time.sleep(0.033)  # ~30 FPS

    def _detect_objects_in_frame(self, frame: np.ndarray, camera_name: str) -> List[DetectedObject]:
        """Detecta objetos en un frame específico."""
        objects = []
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        for color_name, color_config in COLOR_RANGES.items():
            # Crear máscara para el color
            lower = np.array(color_config["lower"])
            upper = np.array(color_config["upper"])
            mask = cv2.inRange(hsv, lower, upper)
            
            # Operaciones morfológicas para mejorar la detección
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < DETECTION_CONFIG['min_area']:
                    continue
                    
                # Filtrar contornos muy pequeños o muy grandes
                if area > 50000:  # Área máxima para evitar detecciones falsas
                    continue
                    
                # Detectar forma
                shape = self._detect_shape(contour)
                if not shape:
                    continue
                    
                # Calcular centro
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                else:
                    continue
                    
                # Calcular confianza basada en el área y forma
                confidence = min(1.0, area / 10000)  # Normalizar confianza
                
                # Crear objeto detectado
                object_id = f"{color_name}_{shape}_{camera_name}_{len(objects)}"
                detected_object = DetectedObject(
                    id=object_id,
                    shape=shape,
                    color=color_name,
                    center=(cx, cy),
                    area=area,
                    confidence=confidence,
                    camera=camera_name
                )
                
                objects.append(detected_object)
                
                # Limitar número de objetos por color
                if len([obj for obj in objects if obj.color == color_name]) >= 3:
                    break
                    
        return objects

    def _detect_shape(self, contour) -> Optional[str]:
        """Detecta la forma geométrica del contorno."""
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        sides = len(approx)
        
        # Calcular área y perímetro
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        # Verificar si es un círculo
        if perimeter > 0:
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity > 0.8:
                return "Circulo"
        
        # Detectar formas basadas en el número de lados
        if sides == 3:
            return "Triangulo"
        elif sides == 4:
            # Verificar si es un cuadrado o rectángulo
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h
            if 0.8 <= aspect_ratio <= 1.2:
                return "Cuadrado"
            else:
                return "Rectangulo"
        elif sides == 5:
            return "Pentagono"
        elif sides == 6:
            return "Hexagono"
        elif sides == 8:
            return "Octagono"
        elif sides > 8:
            # Para formas con muchos lados, verificar si es un círculo
            if circularity > 0.7:
                return "Circulo"
            else:
                return "Poligono"
        
        return None

    def get_detected_objects(self, camera_name: str = None) -> Dict[str, List[DetectedObject]]:
        """Obtiene los objetos detectados."""
        if camera_name:
            return {camera_name: self.detected_objects.get(camera_name, [])}
        return self.detected_objects

    def get_object_by_id(self, object_id: str) -> Optional[DetectedObject]:
        """Obtiene un objeto específico por su ID."""
        for objects in self.detected_objects.values():
            for obj in objects:
                if obj.id == object_id:
                    return obj
        return None

    def get_objects_by_color(self, color: str) -> List[DetectedObject]:
        """Obtiene todos los objetos de un color específico."""
        objects = []
        for obj_list in self.detected_objects.values():
            for obj in obj_list:
                if obj.color == color:
                    objects.append(obj)
        return objects

    def get_objects_by_shape(self, shape: str) -> List[DetectedObject]:
        """Obtiene todos los objetos de una forma específica."""
        objects = []
        for obj_list in self.detected_objects.values():
            for obj in obj_list:
                if obj.shape == shape:
                    objects.append(obj)
        return objects

    def convert_to_world_coordinates(self, pixel_coords: Tuple[int, int], camera_name: str) -> Tuple[float, float, float]:
        """Convierte coordenadas de píxeles a coordenadas del mundo real."""
        # Esta función requeriría calibración de cámara
        # Por ahora, usamos una conversión simple
        x, y = pixel_coords
        
        # Convertir a coordenadas del brazo (mm)
        # Estos valores deberían calibrarse para cada cámara
        if camera_name == "camera_x":
            world_x = (x - 320) * 0.5  # Factor de escala
            world_y = 0  # La cámara X no ve el eje Y
            world_z = 0  # Altura fija
        elif camera_name == "camera_y":
            world_x = 0  # La cámara Y no ve el eje X
            world_y = (y - 240) * 0.5  # Factor de escala
            world_z = 0  # Altura fija
        else:
            world_x = world_y = world_z = 0
            
        return (world_x, world_y, world_z)

    def calibrate_with_reference(self, reference_length_cm: float, measured_pixels: float):
        """Calibración usando un objeto de referencia de tamaño conocido."""
        pixels_per_cm = measured_pixels / reference_length_cm
        
        for camera_name in self.cameras_initialized:
            if self.cameras_initialized[camera_name]:
                self.pixels_per_cm[camera_name] = pixels_per_cm
        
        print(f"Calibrado usando referencia: {pixels_per_cm:.2f} px/cm")
        self.is_calibrated = True

    def pixels_to_cm(self, pixels: float, camera_name: str) -> float:
        """Convierte píxeles a centímetros."""
        if not self.is_calibrated or camera_name not in self.pixels_per_cm:
            return pixels  # Retornar píxeles si no está calibrado
        
        return pixels / self.pixels_per_cm[camera_name]

    def cm_to_pixels(self, cm: float, camera_name: str) -> float:
        """Convierte centímetros a píxeles."""
        if not self.is_calibrated or camera_name not in self.pixels_per_cm:
            return cm  # Retornar cm si no está calibrado
        
        return cm * self.pixels_per_cm[camera_name]

    def calculate_distance_cm(self, point1: Tuple[int, int], point2: Tuple[int, int], camera_name: str) -> float:
        """Calcula la distancia en centímetros entre dos puntos."""
        distance_pixels = self.calculate_distance(point1, point2)
        return self.pixels_to_cm(distance_pixels, camera_name)

    def draw_coordinate_grid(self, frame: np.ndarray, camera_name: str) -> np.ndarray:
        """Dibuja una rejilla de coordenadas en el frame."""
        height, width = frame.shape[:2]
        
        # Configuración de la rejilla
        grid_spacing = 50  # Píxeles entre líneas de la rejilla
        grid_color = (128, 128, 128)  # Color gris
        grid_thickness = 1
        
        # Dibujar líneas verticales
        for x in range(0, width, grid_spacing):
            cv2.line(frame, (x, 0), (x, height), grid_color, grid_thickness)
            # Agregar etiquetas de coordenadas X
            if x > 0:  # No etiquetar el borde izquierdo
                if self.is_calibrated and camera_name in self.pixels_per_cm:
                    # Mostrar en centímetros
                    cm_x = self.pixels_to_cm(x, camera_name)
                    label_text = f"{cm_x:.1f}cm"
                else:
                    # Mostrar en píxeles
                    label_text = str(x)
                cv2.putText(frame, label_text, (x + 5, 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Dibujar líneas horizontales
        for y in range(0, height, grid_spacing):
            cv2.line(frame, (0, y), (width, y), grid_color, grid_thickness)
            # Agregar etiquetas de coordenadas Y
            if y > 0:  # No etiquetar el borde superior
                if self.is_calibrated and camera_name in self.pixels_per_cm:
                    # Mostrar en centímetros
                    cm_y = self.pixels_to_cm(y, camera_name)
                    label_text = f"{cm_y:.1f}cm"
                else:
                    # Mostrar en píxeles
                    label_text = str(y)
                cv2.putText(frame, label_text, (5, y - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Dibujar ejes principales (más gruesos)
        center_x, center_y = width // 2, height // 2
        cv2.line(frame, (center_x, 0), (center_x, height), (255, 255, 255), 2)  # Eje Y
        cv2.line(frame, (0, center_y), (width, center_y), (255, 255, 255), 2)   # Eje X
        
        # Etiquetar el centro
        cv2.putText(frame, "O", (center_x + 5, center_y - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Agregar información de la cámara
        camera_info = f"Camara: {camera_name}"
        if self.is_calibrated and camera_name in self.pixels_per_cm:
            camera_info += f" | Altura: {self.camera_height}cm | {self.pixels_per_cm[camera_name]:.1f}px/cm"
        cv2.putText(frame, camera_info, (10, height - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame

    def get_frame(self, camera_name: str) -> Optional[np.ndarray]:
        """Obtiene un frame sin detecciones (más rápido)."""
        if camera_name not in self.cameras_initialized or not self.cameras_initialized[camera_name]:
            return None
            
        if self.current_frames[camera_name] is None:
            return None
            
        # Usar el frame actual de esta cámara específica
        with self.frame_locks[camera_name]:
            if self.current_frames[camera_name] is None:
                return None
            frame = self.current_frames[camera_name].copy()
            
        return frame

    def calculate_distance(self, point1: Tuple[int, int], point2: Tuple[int, int]) -> float:
        """Calcula la distancia euclidiana entre dos puntos."""
        return np.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

    def draw_connections_between_squares(self, frame: np.ndarray, objects: List[DetectedObject]) -> np.ndarray:
        """Dibuja líneas entre cuadrados detectados y muestra las distancias."""
        # Filtrar solo cuadrados
        squares = [obj for obj in objects if obj.shape in ["Cuadrado", "Rectangulo"]]
        
        if len(squares) < 2:
            return frame
        
        # Obtener nombre de la cámara del primer objeto
        camera_name = squares[0].camera if squares else None
        
        # Dibujar conexiones entre todos los cuadrados
        for i in range(len(squares)):
            for j in range(i + 1, len(squares)):
                square1 = squares[i]
                square2 = squares[j]
                
                # Calcular distancia
                if self.is_calibrated and camera_name:
                    distance = self.calculate_distance_cm(square1.center, square2.center, camera_name)
                    distance_text = f"{distance:.1f}cm"
                else:
                    distance = self.calculate_distance(square1.center, square2.center)
                    distance_text = f"{distance:.1f}px"
                
                # Color de la línea (usar color del primer cuadrado)
                line_color = COLOR_RANGES[square1.color]["bgr"]
                
                # Dibujar línea
                cv2.line(frame, square1.center, square2.center, line_color, 2)
                
                # Calcular punto medio para mostrar la distancia
                mid_x = (square1.center[0] + square2.center[0]) // 2
                mid_y = (square1.center[1] + square2.center[1]) // 2
                
                # Fondo para el texto
                text_size = cv2.getTextSize(distance_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                text_x = mid_x - text_size[0] // 2
                text_y = mid_y + text_size[1] // 2
                
                # Dibujar rectángulo de fondo
                cv2.rectangle(frame, 
                             (text_x - 5, text_y - text_size[1] - 5),
                             (text_x + text_size[0] + 5, text_y + 5),
                             (0, 0, 0), -1)
                
                # Dibujar texto de distancia
                cv2.putText(frame, distance_text, 
                           (text_x, text_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 
                           0.5, (255, 255, 255), 2)
        
        return frame

    def get_frame_with_detections(self, camera_name: str) -> Optional[np.ndarray]:
        """Obtiene un frame con las detecciones dibujadas."""
        if camera_name not in self.cameras_initialized or not self.cameras_initialized[camera_name]:
            return None
            
        if self.current_frames[camera_name] is None:
            return None
            
        # Usar el frame actual de esta cámara específica
        with self.frame_locks[camera_name]:
            if self.current_frames[camera_name] is None:
                return None
            frame = self.current_frames[camera_name].copy()
            
        # Dibujar rejilla de coordenadas
        frame = self.draw_coordinate_grid(frame, camera_name)
            
        # Dibujar objetos detectados
        objects = self.detected_objects.get(camera_name, [])
        for obj in objects:
            # Dibujar caja
            x, y = obj.center
            color_bgr = COLOR_RANGES[obj.color]["bgr"]
            
            # Tamaño de la caja basado en el área
            size = int(np.sqrt(obj.area) / 2)
            cv2.rectangle(frame, 
                         (x - size, y - size), 
                         (x + size, y + size), 
                         color_bgr, 2)
            
            # Dibujar texto
            text = f"{obj.shape} {obj.color}"
            cv2.putText(frame, text, 
                       (x - size, y - size - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       0.6, color_bgr, 2)
            
            # Dibujar ID
            cv2.putText(frame, obj.id, 
                       (x - size, y + size + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       0.4, (255, 255, 255), 1)
            
            # Dibujar coordenadas del objeto
            if self.is_calibrated and camera_name in self.pixels_per_cm:
                # Mostrar coordenadas en centímetros
                cm_x = self.pixels_to_cm(x, camera_name)
                cm_y = self.pixels_to_cm(y, camera_name)
                coord_text = f"({cm_x:.1f}cm, {cm_y:.1f}cm)"
            else:
                # Mostrar coordenadas en píxeles
                coord_text = f"({x}, {y})"
            cv2.putText(frame, coord_text, 
                       (x - size, y + size + 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       0.4, (255, 255, 255), 1)
        
        # Dibujar conexiones entre cuadrados
        frame = self.draw_connections_between_squares(frame, objects)
        
        return frame

    def get_frame_with_grid(self, camera_name: str) -> Optional[np.ndarray]:
        """Obtiene un frame con solo la rejilla de coordenadas (sin detecciones)."""
        if camera_name not in self.cameras_initialized or not self.cameras_initialized[camera_name]:
            return None
            
        if self.current_frames[camera_name] is None:
            return None
            
        # Usar el frame actual de esta cámara específica
        with self.frame_locks[camera_name]:
            if self.current_frames[camera_name] is None:
                return None
            frame = self.current_frames[camera_name].copy()
            
        # Dibujar rejilla de coordenadas
        frame = self.draw_coordinate_grid(frame, camera_name)
        
        return frame

    def get_status(self):
        """Obtiene el estado del sistema de visión."""
        status = {}
        for camera_name, initialized in self.cameras_initialized.items():
            status[camera_name] = {
                'is_running': self.is_running,
                'has_frame': self.current_frames[camera_name] is not None,
                'camera_opened': self.cameras[camera_name].isOpened() if self.cameras[camera_name] else False
            }
        return status

    def calibrate_cameras(self):
        """Calibra las cámaras usando un patrón de calibración."""
        # Implementar calibración de cámara usando OpenCV
        # Por ahora es un placeholder
        print("🔧 Función de calibración no implementada")

    def save_calibration(self, filename: str):
        """Guarda la calibración de las cámaras."""
        if self.calibration_matrix is not None:
            np.save(filename, self.calibration_matrix)
            print(f"💾 Calibración guardada en {filename}")

    def load_calibration(self, filename: str):
        """Carga la calibración de las cámaras."""
        try:
            self.calibration_matrix = np.load(filename)
            print(f"📂 Calibración cargada desde {filename}")
        except Exception as e:
            print(f"❌ Error al cargar calibración: {e}")

    def __del__(self):
        """Destructor para liberar recursos."""
        self.stop_detection()
