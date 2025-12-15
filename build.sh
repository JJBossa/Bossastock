#!/usr/bin/env bash
# Build script para Render

# Instalar dependencias de Python
pip install -r requirements.txt

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Nota: Tesseract y poppler-utils se instalan automáticamente en Render
# Si necesitas instalarlos manualmente, Render usa apt-get pero requiere configuración especial
# Por ahora, Render debería tenerlos preinstalados

