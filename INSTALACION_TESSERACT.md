# Instalación de Tesseract OCR

Para que el sistema de facturas funcione correctamente, necesitas instalar Tesseract OCR en tu sistema.

## Windows

### Opción 1: Instalador oficial (Recomendado)

1. Descarga el instalador desde: https://github.com/UB-Mannheim/tesseract/wiki
2. Ejecuta el instalador y sigue las instrucciones
3. Durante la instalación, asegúrate de instalar el paquete de idioma español
4. Por defecto se instala en: `C:\Program Files\Tesseract-OCR\`

### Opción 2: Usando Chocolatey

```bash
choco install tesseract
```

### Verificar instalación

Abre PowerShell y ejecuta:
```bash
tesseract --version
```

Si aparece la versión, está instalado correctamente.

### Configurar ruta (si es necesario)

Si Tesseract no está en el PATH, descomenta y ajusta esta línea en `inventario/utils_ocr.py`:

```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-spa  # Para español
```

## macOS

```bash
brew install tesseract
brew install tesseract-lang  # Para idiomas adicionales
```

## Verificar que funciona

Después de instalar, reinicia el servidor Django y prueba subir una factura.

## Nota

Si no puedes instalar Tesseract, el sistema seguirá funcionando pero no podrá procesar facturas automáticamente. Podrás subir facturas y agregar items manualmente.

