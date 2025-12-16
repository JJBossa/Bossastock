#!/usr/bin/env bash
# Build script para Render

set -o errexit  # Exit on error

# Opcional: Instalar Tesseract OCR (descomenta si necesitas OCR)
# apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-spa

# Instalar dependencias Python
pip install -r requirements.txt

# Recolectar archivos estáticos
python manage.py collectstatic --no-input --clear

# Ejecutar migraciones
python manage.py migrate --no-input

