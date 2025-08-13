#!/bin/bash

# Script de instalación para Sistema de Control de Brazo Robótico SCARA
# Compatible con Ubuntu/Debian y derivados

echo "🤖 Instalando Sistema de Control de Brazo Robótico SCARA"
echo "=================================================="

# Verificar si Python 3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado. Instalando..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-tk
else
    echo "✅ Python 3 ya está instalado"
fi

# Verificar si pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 no está instalado. Instalando..."
    sudo apt install -y python3-pip
else
    echo "✅ pip3 ya está instalado"
fi

# Instalar dependencias del sistema
echo "📦 Instalando dependencias del sistema..."
sudo apt update
sudo apt install -y \
    python3-opencv \
    python3-numpy \
    python3-serial \
    python3-pil \
    libgl1-mesa-glx \
    libglib2.0-0

# Instalar dependencias de Python
echo "🐍 Instalando dependencias de Python..."
pip3 install -r requirements.txt

# Crear directorio para calibraciones
mkdir -p calibrations

# Configurar permisos para puertos seriales
echo "🔧 Configurando permisos para puertos seriales..."
sudo usermod -a -G dialout $USER

# Crear script de inicio
echo "📝 Creando script de inicio..."
cat > start_robot.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
python3 main.py "$@"
EOF

chmod +x start_robot.sh

# Crear acceso directo en escritorio (opcional)
if [ -d "$HOME/Desktop" ]; then
    echo "🖥️ Creando acceso directo en escritorio..."
    cat > "$HOME/Desktop/SCARA-Robot.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SCARA Robot Control
Comment=Sistema de Control de Brazo Robótico SCARA
Exec=$(pwd)/start_robot.sh
Icon=applications-engineering
Terminal=true
Categories=Science;Engineering;
EOF
    chmod +x "$HOME/Desktop/SCARA-Robot.desktop"
fi

echo ""
echo "✅ Instalación completada exitosamente!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Conectar el ESP32 al puerto USB"
echo "2. Subir el código esp32_controller.ino al ESP32"
echo "3. Conectar las cámaras USB"
echo "4. Ejecutar: ./start_robot.sh"
echo ""
echo "🔧 Configuración adicional:"
echo "- Editar config.py para ajustar puerto y configuración"
echo "- Calibrar cámaras desde la interfaz"
echo "- Configurar límites del workspace según tu hardware"
echo ""
echo "📚 Documentación: README.md"
echo "🐛 Soporte: Crear issue en GitHub"
