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
        """Inicializa el sistema de visión artificial con dos cámaras."""
        self.cameras = {}
        self.detected_objects = {}
        self.is_running = False
        self.calibration_matrix = None
        self.camera_threads = {}
        
        # Inicializar cámaras
        self._initialize_cameras()
        
    def _initialize_cameras(self):
        """Inicializa las dos cámaras."""
        for camera_name, config in CAMERA_CONFIG.items():
            try:
                cap = cv2.VideoCapture(config['index'])
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config['resolution'][0])
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config['resolution'][1])
                    cap.set(cv2.CAP_PROP_FPS, config['fps'])
                    self.cameras[camera_name] = cap
                    print(f"✅ Cámara {camera_name} inicializada correctamente")
                else:
                    print(f"❌ No se pudo abrir la cámara {camera_name}")
            except Exception as e:
                print(f"❌ Error al inicializar cámara {camera_name}: {e}")

    def start_detection(self):
        """Inicia la detección continua en ambas cámaras."""
        if self.is_running:
            return
            
        self.is_running = True
        
        for camera_name in self.cameras.keys():
            thread = threading.Thread(
                target=self._detection_loop,
                args=(camera_name,),
                daemon=True
            )
            self.camera_threads[camera_name] = thread
            thread.start()
            
        print("🔍 Sistema de visión iniciado")

    def stop_detection(self):
        """Detiene la detección continua."""
        self.is_running = False
        
        # Esperar a que terminen los threads
        for thread in self.camera_threads.values():
            thread.join(timeout=2)
            
        # Liberar cámaras
        for cap in self.cameras.values():
            cap.release()
            
        print("🛑 Sistema de visión detenido")

    def _detection_loop(self, camera_name: str):
        """Loop de detección para una cámara específica."""
        cap = self.cameras[camera_name]
        
        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                continue
                
            # Detectar objetos en el frame
            objects = self._detect_objects_in_frame(frame, camera_name)
            
            # Actualizar objetos detectados
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
            
            # Operaciones morfológicas
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < DETECTION_CONFIG['min_area']:
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
                
                # Limitar número de objetos
                if len(objects) >= DETECTION_CONFIG['max_objects']:
                    break
                    
        return objects

    def _detect_shape(self, contour) -> Optional[str]:
        """Detecta la forma geométrica del contorno."""
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        sides = len(approx)
        
        if sides == 3:
            return "Triangulo"
        elif sides == 4:
            return "Cuadrado"
        elif sides == 5:
            return "Pentagono"
        else:
            # Verificación para círculos
            area = cv2.contourArea(contour)
            (x, y), radius = cv2.minEnclosingCircle(contour)
            circle_area = np.pi * (radius ** 2)
            if 0.7 <= area/circle_area <= 1.3:
                return "Circulo"
        
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

    def get_frame_with_detections(self, camera_name: str) -> Optional[np.ndarray]:
        """Obtiene un frame con las detecciones dibujadas."""
        if camera_name not in self.cameras:
            return None
            
        cap = self.cameras[camera_name]
        ret, frame = cap.read()
        if not ret:
            return None
            
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
        
        return frame

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
