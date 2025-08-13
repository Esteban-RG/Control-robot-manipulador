import time
import threading
from typing import List, Optional, Dict
from robot_actions import RobotActions
from vision_system import VisionSystem, DetectedObject
from config import ROBOT_CONFIG

class RobotRoutines:
    def __init__(self, robot_actions: RobotActions, vision_system: VisionSystem = None):
        self.robot_actions = robot_actions
        self.vision_system = vision_system
        self.is_running = False
        self.current_routine = None
        self.routine_thread = None

    def start_routine(self, routine_name: str, *args, **kwargs) -> bool:
        """Inicia una rutina automática en un thread separado."""
        if self.is_running:
            print("⚠️ Ya hay una rutina ejecutándose")
            return False

        routine_method = getattr(self, routine_name, None)
        if not routine_method:
            print(f"❌ Rutina '{routine_name}' no encontrada")
            return False

        self.is_running = True
        self.current_routine = routine_name
        
        self.routine_thread = threading.Thread(
            target=self._run_routine,
            args=(routine_method, args, kwargs),
            daemon=True
        )
        self.routine_thread.start()
        
        print(f"🤖 Iniciando rutina: {routine_name}")
        return True

    def stop_routine(self):
        """Detiene la rutina actual."""
        self.is_running = False
        if self.routine_thread and self.routine_thread.is_alive():
            self.routine_thread.join(timeout=5)
        self.current_routine = None
        print("🛑 Rutina detenida")

    def _run_routine(self, routine_method, args, kwargs):
        """Ejecuta una rutina en un thread separado."""
        try:
            routine_method(*args, **kwargs)
        except Exception as e:
            print(f"❌ Error en rutina: {e}")
        finally:
            self.is_running = False
            self.current_routine = None

    def square_routine(self, size: float = 50.0, speed: int = 50):
        """Rutina para que el robot haga un cuadrado."""
        print("🔲 Ejecutando rutina: Cuadrado")
        
        # Ir a posición inicial
        self.robot_actions.move_to_position(0, 0, 20, speed)
        
        # Dibujar cuadrado
        positions = [
            (size, 0, 20),
            (size, size, 20),
            (0, size, 20),
            (0, 0, 20)
        ]
        
        for x, y, z in positions:
            if not self.is_running:
                break
            self.robot_actions.move_to_position(x, y, z, speed)
            time.sleep(1)
        
        print("✅ Rutina cuadrado completada")

    def circle_routine(self, radius: float = 30.0, speed: int = 50, steps: int = 16):
        """Rutina para que el robot haga un círculo."""
        print("⭕ Ejecutando rutina: Círculo")
        
        import math
        
        # Ir a posición inicial
        self.robot_actions.move_to_position(radius, 0, 20, speed)
        
        # Dibujar círculo
        for i in range(steps + 1):
            if not self.is_running:
                break
            angle = 2 * math.pi * i / steps
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            self.robot_actions.move_to_position(x, y, 20, speed)
            time.sleep(0.5)
        
        print("✅ Rutina círculo completada")

    def pick_and_place_routine(self, pick_x: float, pick_y: float, place_x: float, place_y: float):
        """Rutina automática de recogida y colocación."""
        print(f"🤖 Ejecutando rutina: Pick & Place")
        
        success = self.robot_actions.pick_and_place(pick_x, pick_y, place_x, place_y)
        
        if success:
            print("✅ Rutina pick & place completada")
        else:
            print("❌ Error en rutina pick & place")

    def vision_pick_routine(self, target_color: str = None, target_shape: str = None):
        """Rutina de recogida basada en visión artificial."""
        if not self.vision_system:
            print("❌ Sistema de visión no disponible")
            return

        print(f"👁️ Ejecutando rutina: Vision Pick")
        
        # Obtener objetos detectados
        detected_objects = self.vision_system.get_detected_objects()
        
        # Filtrar objetos según criterios
        target_objects = []
        for camera_name, objects in detected_objects.items():
            for obj in objects:
                if target_color and obj.color != target_color:
                    continue
                if target_shape and obj.shape != target_shape:
                    continue
                target_objects.append(obj)
        
        if not target_objects:
            print("❌ No se encontraron objetos que coincidan con los criterios")
            return
        
        # Ordenar por confianza
        target_objects.sort(key=lambda x: x.confidence, reverse=True)
        target = target_objects[0]
        
        print(f"🎯 Objetivo seleccionado: {target.id} ({target.color} {target.shape})")
        
        # Convertir coordenadas de píxeles a coordenadas del mundo
        world_coords = self.vision_system.convert_to_world_coordinates(
            target.center, target.camera
        )
        
        # Ejecutar recogida
        success = self.robot_actions.auto_pick(world_coords[0], world_coords[1])
        
        if success:
            print("✅ Recogida por visión completada")
        else:
            print("❌ Error en recogida por visión")

    def sorting_routine(self):
        """Rutina de clasificación automática de objetos."""
        if not self.vision_system:
            print("❌ Sistema de visión no disponible")
            return

        print("📦 Ejecutando rutina: Clasificación")
        
        # Posiciones de clasificación por color
        sorting_positions = {
            'red': (50, 50),
            'green': (50, -50),
            'blue': (-50, 50),
            'yellow': (-50, -50)
        }
        
        # Obtener todos los objetos
        all_objects = []
        for objects in self.vision_system.get_detected_objects().values():
            all_objects.extend(objects)
        
        # Clasificar por color
        for obj in all_objects:
            if not self.is_running:
                break
                
            if obj.color in sorting_positions:
                place_x, place_y = sorting_positions[obj.color]
                
                # Convertir coordenadas
                world_coords = self.vision_system.convert_to_world_coordinates(
                    obj.center, obj.camera
                )
                
                # Ejecutar pick & place
                success = self.robot_actions.pick_and_place(
                    world_coords[0], world_coords[1],
                    place_x, place_y
                )
                
                if success:
                    print(f"✅ Objeto {obj.color} clasificado")
                else:
                    print(f"❌ Error clasificando objeto {obj.color}")
                
                time.sleep(2)  # Pausa entre objetos
        
        print("✅ Rutina de clasificación completada")

    def inspection_routine(self, inspection_points: List[tuple] = None):
        """Rutina de inspección automática."""
        print("🔍 Ejecutando rutina: Inspección")
        
        # Puntos de inspección por defecto
        if not inspection_points:
            inspection_points = [
                (0, 0, 30),
                (50, 0, 30),
                (0, 50, 30),
                (-50, 0, 30),
                (0, -50, 30)
            ]
        
        for i, (x, y, z) in enumerate(inspection_points):
            if not self.is_running:
                break
                
            print(f"🔍 Punto de inspección {i+1}/{len(inspection_points)}")
            self.robot_actions.move_to_position(x, y, z, speed=30)
            
            # Simular inspección
            time.sleep(3)
            
            # Aquí se podría integrar con el sistema de visión
            if self.vision_system:
                detected_objects = self.vision_system.get_detected_objects()
                print(f"📊 Objetos detectados en punto {i+1}: {len(detected_objects)}")
        
        print("✅ Rutina de inspección completada")

    def calibration_routine(self):
        """Rutina de calibración del brazo."""
        print("🔧 Ejecutando rutina: Calibración")
        
        # Ir a posición home
        self.robot_actions.home_position()
        time.sleep(2)
        
        # Verificar límites del workspace
        limits = ROBOT_CONFIG['workspace_limits']
        test_positions = [
            (limits['x_min'], 0, 20),
            (limits['x_max'], 0, 20),
            (0, limits['y_min'], 20),
            (0, limits['y_max'], 20),
            (0, 0, limits['z_min']),
            (0, 0, limits['z_max'])
        ]
        
        for x, y, z in test_positions:
            if not self.is_running:
                break
            print(f"🔧 Probando posición: ({x}, {y}, {z})")
            self.robot_actions.move_to_position(x, y, z, speed=20)
            time.sleep(1)
        
        # Volver a home
        self.robot_actions.home_position()
        
        print("✅ Rutina de calibración completada")

    def get_routine_status(self) -> Dict:
        """Obtiene el estado de las rutinas."""
        return {
            'is_running': self.is_running,
            'current_routine': self.current_routine,
            'robot_position': self.robot_actions.get_current_position()
        }

    def emergency_stop(self):
        """Parada de emergencia."""
        print("🚨 PARADA DE EMERGENCIA")
        self.stop_routine()
        self.robot_actions.emergency_stop()