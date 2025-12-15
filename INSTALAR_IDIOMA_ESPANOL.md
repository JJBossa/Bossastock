# Instalar Idioma Español en Tesseract OCR

## ⚠️ PROBLEMA DETECTADO

Tu instalación de Tesseract **NO tiene el idioma español instalado**. Solo tiene:
- `eng` (inglés)
- `osd` (detección de orientación)

Esto afecta la precisión del OCR para facturas en español.

## Solución: Instalar Idioma Español

### Opción 1: Reinstalar Tesseract con Español (Recomendado)

1. **Descarga el instalador completo** desde:
   https://github.com/UB-Mannheim/tesseract/wiki

2. **Ejecuta el instalador** y durante la instalación:
   - ✅ Marca la opción **"Spanish"** en la lista de idiomas adicionales
   - Asegúrate de que esté seleccionado antes de continuar

3. **Completa la instalación**

4. **Verifica la instalación:**
   ```bash
   tesseract --list-langs
   ```
   
   Deberías ver `spa` en la lista.

### Opción 2: Descargar Manualmente el Archivo de Idioma

1. **Descarga el archivo `spa.traineddata`** desde:
   https://github.com/tesseract-ocr/tessdata/blob/main/spa.traineddata

2. **Copia el archivo** a la carpeta de datos de Tesseract:
   ```
   C:\Program Files\Tesseract-OCR\tessdata\
   ```

3. **Verifica la instalación:**
   ```bash
   tesseract --list-langs
   ```
   
   Deberías ver `spa` en la lista.

### Opción 3: Usando PowerShell (Rápido)

```powershell
# Descargar el archivo de idioma español
$url = "https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata"
$output = "C:\Program Files\Tesseract-OCR\tessdata\spa.traineddata"

# Crear carpeta si no existe
New-Item -ItemType Directory -Force -Path "C:\Program Files\Tesseract-OCR\tessdata"

# Descargar
Invoke-WebRequest -Uri $url -OutFile $output

# Verificar
tesseract --list-langs
```

## Verificación

Después de instalar, ejecuta:

```bash
tesseract --list-langs
```

Deberías ver algo como:
```
List of available languages (3):
eng
osd
spa    <-- Este debe aparecer
```

## Nota Importante

El código del sistema **ya está preparado** para funcionar sin español (usará inglés como fallback), pero:
- ⚠️ La precisión será **menor** con inglés
- ⚠️ Los caracteres especiales en español (ñ, acentos) pueden no detectarse bien
- ✅ **Recomendado:** Instalar español para mejor precisión

## Después de Instalar

1. Reinicia el servidor Django si está corriendo
2. Prueba subir la factura nuevamente
3. El sistema detectará automáticamente que español está disponible

