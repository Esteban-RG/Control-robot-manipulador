import cv2
import numpy as np

# Configuración de colores en HSV (Hue, Saturation, Value)
COLOR_RANGES = {
    "red":    {"lower": [0, 100, 100],   "upper": [10, 255, 255]},
    "yellow": {"lower": [20, 100, 100],  "upper": [40, 255, 255]},
    "green":  {"lower": [50, 100, 100],  "upper": [80, 255, 255]},
    "blue":   {"lower": [100, 100, 100], "upper": [130, 255, 255]}
}

# Mapeo de formas a colores
SHAPE_COLORS = {
    "Circulo":   (0, 0, 255),     # Rojo en BGR
    "Triangulo": (0, 255, 255),   # Amarillo
    "Cuadrado":  (0, 255, 0),     # Verde
    "Pentagono": (255, 0, 0)      # Azul
}

def detect_shape(contour):
    """Detecta la forma geométrica del contorno"""
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
        # Verificación adicional para círculos
        area = cv2.contourArea(contour)
        (x, y), radius = cv2.minEnclosingCircle(contour)
        circle_area = np.pi * (radius ** 2)
        return "Circulo" if 0.7 <= area/circle_area <= 1.3 else None

def detect_objects(frame):
    """Detección principal de objetos"""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    processed_frame = frame.copy()
    
    # Almacenar centros de las figuras
    centers = {"Cuadrado": None, "Pentagono": None}
    
    for color_name, color_range in COLOR_RANGES.items():
        # Crear máscara para cada color
        lower = np.array(color_range["lower"])
        upper = np.array(color_range["upper"])
        mask = cv2.inRange(hsv, lower, upper)
        
        # Operaciones morfológicas para limpiar la máscara
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7,7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            if cv2.contourArea(contour) < 500:  # Filtrar pequeños ruidos
                continue
                
            shape = detect_shape(contour)
            if not shape:
                continue
                
            # Dibujar caja y texto
            x, y, w, h = cv2.boundingRect(contour)
            box_color = SHAPE_COLORS.get(shape, (255,255,255))
            
            # Grosor dinámico según el tamaño
            thickness = max(1, int(min(w,h)*0.01))
            
            cv2.rectangle(processed_frame, 
                         (x, y), (x+w, y+h),
                         box_color, thickness)
            
            cv2.putText(processed_frame, 
                       f"{shape} {color_name.capitalize()}",
                       (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       0.7, box_color, thickness)
            
            # Guardar el centro de la figura
            center = (int(x + w/2), int(y + h/2))
            if shape in centers:
                centers[shape] = center
    
    # Dibujar línea entre el cuadrado verde y el pentágono azul
    if centers["Cuadrado"] and centers["Pentagono"]:
        cv2.line(processed_frame, 
                centers["Cuadrado"], centers["Pentagono"], 
                (255, 255, 255), 2)  # Línea blanca de grosor 2
    
    return processed_frame

def main():
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error al abrir la cámara")
        return
    
    cv2.namedWindow("Detección Mejorada", cv2.WINDOW_NORMAL)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        output = detect_objects(frame)
        
        cv2.imshow("Detección Mejorada", output)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()