# Diagnóstico y Soluciones para OCR de Facturas

## Problemas Comunes y Soluciones

### 1. **Tesseract OCR no está instalado o no está en el PATH**

**Síntoma:** No se extrae ningún texto o error al procesar.

**Solución:**
```bash
# Windows: Descargar e instalar desde:
https://github.com/UB-Mannheim/tesseract/wiki

# Durante la instalación, asegúrate de instalar el paquete de idioma español
# Por defecto se instala en: C:\Program Files\Tesseract-OCR\

# Verificar instalación:
tesseract --version
```

**Verificar en el código:**
- El archivo `inventario/utils_ocr.py` busca Tesseract en la ruta por defecto
- Si está en otra ubicación, edita la línea 16-18 del archivo

---

### 2. **El paquete de idioma español no está instalado**

**Síntoma:** Se extrae texto pero con muchos errores o caracteres incorrectos.

**Solución:**
```bash
# Windows: Reinstalar Tesseract y seleccionar "Spanish" en los idiomas
# O descargar el archivo .traineddata desde:
https://github.com/tesseract-ocr/tessdata

# Colocar el archivo spa.traineddata en:
C:\Program Files\Tesseract-OCR\tessdata\
```

---

### 3. **OpenCV no está instalado (opcional pero recomendado)**

**Síntoma:** El OCR funciona pero con menor precisión.

**Solución:**
```bash
pip install opencv-python
```

**Nota:** El sistema funciona sin OpenCV, pero la calidad del OCR será mejor con él instalado.

---

### 4. **La imagen es de baja calidad o está rotada**

**Síntoma:** Se extrae texto pero con muchos errores.

**Soluciones:**
- Asegúrate de que la imagen esté en formato JPG o PNG
- La imagen debe estar en orientación correcta (no rotada)
- Mejor calidad = mejor OCR (mínimo 300 DPI recomendado)
- Evita imágenes muy oscuras o con mucho ruido

---

### 5. **El formato de la factura no coincide con los patrones esperados**

**Síntoma:** Se extrae texto pero no se detectan items.

**El código actual busca:**
- Líneas que comienzan con código de producto (5-6 dígitos)
- Precios con formato chileno: `19.000` o `19.000,00`
- Tabla de productos con columnas: Código | Descripción | Precio

**Si tu factura tiene otro formato:**
- Revisa el texto extraído en la pantalla de edición (botón "Ver Texto Extraído (OCR)")
- Puedes agregar items manualmente si el OCR no los detecta automáticamente

---

### 6. **Problemas de permisos o rutas de archivos**

**Síntoma:** Error al procesar la imagen.

**Solución:**
- Verifica que Django tenga permisos de lectura en la carpeta `media/`
- Verifica que la ruta del archivo sea correcta
- En Windows, asegúrate de que las rutas no tengan caracteres especiales

---

## Cómo Diagnosticar Problemas

### Paso 1: Verificar que Tesseract funciona
```bash
tesseract --version
```

### Paso 2: Probar OCR manualmente
```bash
tesseract imagen.jpg output.txt -l spa
```

### Paso 3: Revisar el texto extraído
1. Sube la factura en el sistema
2. Ve a "Editar Factura"
3. Haz clic en "Ver Texto Extraído (OCR)"
4. Revisa qué texto se extrajo

### Paso 4: Verificar en la consola del servidor
Los errores detallados se muestran en la consola donde ejecutas `python manage.py runserver`

---

## Mejoras Implementadas en el Código

### 1. **Múltiples modos PSM (Page Segmentation Mode)**
- PSM 11: Para texto disperso (tablas)
- PSM 6: Para bloques uniformes
- PSM 4: Para columnas simples
- El sistema prueba todos y usa el mejor resultado

### 2. **Preprocesamiento mejorado**
- Aumento de contraste (CLAHE o equalizeHist)
- Reducción de ruido (medianBlur)
- Binarización adaptativa optimizada

### 3. **Extracción de items mejorada**
- Detecta inicio y fin de tabla de productos
- Maneja precios con formato `19.000,00` y `19.000`
- Extrae nombres de productos más precisamente
- Maneja múltiples formatos de facturas

### 4. **Manejo de errores robusto**
- Funciona con o sin OpenCV
- Muestra mensajes informativos al usuario
- Permite agregar items manualmente si falla el OCR

---

## Checklist de Verificación

- [ ] Tesseract OCR instalado
- [ ] Paquete de idioma español instalado
- [ ] OpenCV instalado (opcional pero recomendado)
- [ ] Ruta de Tesseract configurada correctamente
- [ ] Imagen en formato JPG/PNG
- [ ] Imagen con buena calidad (mínimo 300 DPI)
- [ ] Imagen en orientación correcta
- [ ] Permisos de lectura en carpeta media/

---

## Si Nada Funciona

1. **Revisa el texto extraído** en la interfaz web
2. **Agrega items manualmente** - El sistema permite esto
3. **Verifica los logs** en la consola del servidor
4. **Prueba con otra factura** para ver si es un problema específico de esa imagen

---

## Contacto y Soporte

Si después de seguir estos pasos el problema persiste, proporciona:
- El texto extraído (visible en la interfaz)
- Los mensajes de error de la consola
- Una descripción del formato de tu factura

