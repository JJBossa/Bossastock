import pytesseract
import re
import os
from PIL import Image

# Intentar importar cv2 (opcional)
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# Intentar importar pdf2image (para PDFs)
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

# ⚠️ IMPORTANTE: ruta correcta en Windows
# Configurar ruta de Tesseract si está en la ubicación por defecto de Windows
if os.name == 'nt':  # Windows
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Idioma a usar para OCR (español + inglés para mejor detección)
# Usar múltiples idiomas mejora la detección de números y caracteres especiales
OCR_LANG = "spa+eng"  # Español + Inglés para mejor detección de números y caracteres


def procesar_imagen_ocr(img, usar_color=False):
    """
    Procesa una imagen (PIL o numpy array) con OCR.
    
    Args:
        img: Imagen PIL o numpy array
        usar_color: Si True, intenta procesar en color (mejor para algunas facturas)
    
    Returns:
        str: Texto extraído
    """
    try:
        # Procesar con Tesseract directamente
        texto = pytesseract.image_to_string(
            img,
            lang=OCR_LANG,
            config=f"--psm 6 --oem 3"
        )
        return texto.strip()
    except Exception as e:
        print(f"Error en OCR: {str(e)}")
        return ""


def extraer_texto_ocr(ruta_archivo):
    """
    Recibe la ruta de una imagen o PDF y devuelve el texto OCR.
    Soporta: JPG, PNG, PDF
    Optimizado para facturas chilenas con tablas.
    """
    # Verificar que el archivo existe
    if not os.path.exists(ruta_archivo):
        return ""
    
    try:
        # Verificar si es PDF
        if ruta_archivo.lower().endswith('.pdf'):
            if not PDF2IMAGE_AVAILABLE:
                return ""
            
            try:
                # Convertir PDF a imágenes (alta resolución para mejor OCR)
                # Aumentar DPI para mejor calidad en facturas
                images = convert_from_path(ruta_archivo, dpi=350, first_page=1, last_page=1)
                
                if not images:
                    return ""
                
                # Procesar la primera página (o todas si es necesario)
                texto_completo = []
                for img in images[:3]:  # Máximo 3 páginas
                    texto = procesar_imagen_ocr(img, usar_color=False)
                    if texto.strip():
                        texto_completo.append(texto)
                
                return "\n".join(texto_completo)
            except Exception as e:
                print(f"Error procesando PDF: {str(e)}")
                return ""
        
        # Es una imagen (JPG, PNG, etc.)
        if CV2_AVAILABLE:
            img = cv2.imread(ruta_archivo)
            if img is None:
                # Intentar con PIL si OpenCV falla
                try:
                    img = Image.open(ruta_archivo)
                except:
                    return ""
            else:
                # Convertir a PIL para compatibilidad
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img_rgb)
        else:
            img = Image.open(ruta_archivo)
        
        # Procesar imagen (optimizado: solo probar sin color primero, color solo si es necesario)
        texto1 = procesar_imagen_ocr(img, usar_color=False)
        
        # Solo probar con color si el resultado sin color es muy corto (probablemente falló)
        if len(texto1) < 200:  # Si el resultado es muy corto, probar con color
            texto2 = procesar_imagen_ocr(img, usar_color=True)
            if len(texto2) > len(texto1) * 1.2:  # Solo usar color si es significativamente mejor
                return texto2
        
        return texto1 if texto1 else ""
            
    except Exception as e:
        print(f"Error en OCR: {str(e)}")
        import traceback
        traceback.print_exc()
        return ""


def extraer_items_factura(texto):
    """
    Extrae items desde texto OCR de facturas.
    Versión simplificada.
    """
    items = []
    
    if not texto or not texto.strip():
        return items

    lineas = texto.split("\n")
    
    for linea in lineas:
        linea = linea.strip()
        if len(linea) < 10:
            continue
        
        # Buscar líneas con códigos y precios
        match_codigo = re.match(r"^(\d{4,8})\s+(.+)", linea)
        if match_codigo:
            resto_linea = match_codigo.group(2)
            
            # Buscar números (precios)
            numeros = re.findall(r"(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?)", resto_linea)
            
            if numeros:
                # Convertir números
                precios = []
                for num_str in numeros:
                    try:
                        num_limpio = num_str.replace(".", "").replace(",", ".")
                        num_valor = float(num_limpio)
                        if 1000 <= num_valor <= 100000:
                            precios.append(int(num_valor))
                    except:
                        continue
                
                if precios:
                    precio = max(precios)
                    cantidad = 1
                    
                    # Extraer nombre básico
                    nombre = resto_linea
                    for num_str in numeros:
                        nombre = nombre.replace(num_str, " ", 1)
                    nombre = re.sub(r'\s+', ' ', nombre).strip()
                    
                    if len(nombre) >= 3:
                        items.append({
                            "nombre": nombre,
                            "cantidad": cantidad,
                            "precio": precio
                        })

    return items
