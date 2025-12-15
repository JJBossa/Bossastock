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

# ⚠️ IMPORTANTE: Configurar ruta de Tesseract según el sistema operativo
# Windows
if os.name == 'nt':  # Windows
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
# Linux (producción - Render, PythonAnywhere, etc.)
else:
    # Intentar encontrar Tesseract en rutas comunes de Linux
    tesseract_paths = [
        '/usr/bin/tesseract',
        '/usr/local/bin/tesseract',
    ]
    for path in tesseract_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break

# Idioma a usar para OCR (español)
OCR_LANG = "spa"


def procesar_imagen_ocr(img, usar_color=False):
    """
    Procesa una imagen (PIL o numpy array) con OCR.
    
    Args:
        img: Imagen PIL o numpy array
        usar_color: Si True, intenta procesar en color (mejor para algunas facturas)
    
    Returns:
        str: Texto extraído
    """
    textos = []
    
    # Convertir PIL a numpy si es necesario
    if isinstance(img, Image.Image) and CV2_AVAILABLE:
        import numpy as np
        img_cv = np.array(img)
        if img_cv.ndim == 3:
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
    elif CV2_AVAILABLE:
        img_cv = img
    else:
        img_cv = None
    
    # Estrategia 1: Procesar en color (si se solicita y es posible)
    if usar_color and CV2_AVAILABLE and img_cv is not None:
        try:
            # Procesar directamente en color (a veces funciona mejor)
            for psm_mode in [11, 6]:
                try:
                    texto = pytesseract.image_to_string(
                        img_cv,
                        lang=OCR_LANG,
                        config=f"--psm {psm_mode}"
                    )
                    if texto.strip():
                        textos.append(texto)
                except:
                    continue
        except:
            pass
    
    # Estrategia 2: Preprocesamiento mejorado (gris con mejoras)
    if CV2_AVAILABLE and img_cv is not None:
        try:
            # Convertir a gris
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Aumentar contraste
            try:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                gray = clahe.apply(gray)
            except:
                gray = cv2.equalizeHist(gray)
            
            # Reducir ruido suavemente
            gray = cv2.medianBlur(gray, 3)
            
            # Probar diferentes métodos de binarización
            estrategias = [
                # Binarización adaptativa
                lambda g: cv2.adaptiveThreshold(
                    g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                ),
                # Otsu threshold
                lambda g: cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
                # Imagen original en gris (sin binarizar)
                lambda g: g,
            ]
            
            for estrategia in estrategias:
                try:
                    processed = estrategia(gray)
                    
                    for psm_mode in [11, 6, 4]:
                        try:
                            texto = pytesseract.image_to_string(
                                processed,
                                lang=OCR_LANG,
                                config=f"--psm {psm_mode}"
                            )
                            if texto.strip() and len(texto.strip()) > 50:  # Solo textos significativos
                                textos.append(texto)
                        except:
                            continue
                except:
                    continue
        except Exception as e:
            print(f"Error en preprocesamiento OpenCV: {str(e)}")
    
    # Estrategia 3: PIL (fallback)
    if isinstance(img, Image.Image):
        try:
            # Probar con imagen original
            for psm_mode in [11, 6]:
                try:
                    texto = pytesseract.image_to_string(
                        img,
                        lang=OCR_LANG,
                        config=f"--psm {psm_mode}"
                    )
                    if texto.strip():
                        textos.append(texto)
                except:
                    pass
            
            # Probar con mejoras de contraste
            from PIL import ImageEnhance
            img_enhanced = ImageEnhance.Contrast(img).enhance(2.0)
            img_enhanced = ImageEnhance.Sharpness(img_enhanced).enhance(2.0)
            
            for psm_mode in [11, 6]:
                try:
                    texto = pytesseract.image_to_string(
                        img_enhanced,
                        lang=OCR_LANG,
                        config=f"--psm {psm_mode}"
                    )
                    if texto.strip():
                        textos.append(texto)
                except:
                    pass
        except:
            pass
    
    # Retornar el mejor texto (más largo y con más palabras)
    if textos:
        # Filtrar textos muy cortos o con muchos caracteres raros
        textos_validos = []
        for t in textos:
            # Contar caracteres alfanuméricos
            alfanumericos = sum(1 for c in t if c.isalnum())
            if alfanumericos > len(t) * 0.3:  # Al menos 30% alfanumérico
                textos_validos.append(t)
        
        if textos_validos:
            # Retornar el más largo y con más palabras
            return max(textos_validos, key=lambda x: (len(x), len(x.split())))
        return max(textos, key=len)
    
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
                # Convertir PDF a imágenes (alta resolución)
                images = convert_from_path(ruta_archivo, dpi=300, first_page=1, last_page=1)
                
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
        
        # Procesar imagen (probar con y sin color)
        texto1 = procesar_imagen_ocr(img, usar_color=False)
        texto2 = procesar_imagen_ocr(img, usar_color=True)
        
        # Retornar el mejor resultado
        if len(texto2) > len(texto1) * 1.1:  # Si color es significativamente mejor
            return texto2
        return texto1 if texto1 else texto2
            
    except Exception as e:
        print(f"Error en OCR: {str(e)}")
        import traceback
        traceback.print_exc()
        return ""


def extraer_items_factura(texto):
    """
    Extrae items desde texto OCR de facturas chilenas.
    Mejorado para detectar múltiples formatos de facturas electrónicas.
    Ahora busca en TODO el texto, no solo en secciones específicas.
    """
    items = []
    
    if not texto or not texto.strip():
        return items

    lineas = texto.split("\n")
    
    # Buscar la sección de productos (después de encabezados)
    en_seccion_productos = False
    encontrado_tabla = False
    skip_next = False  # Para saltar líneas de encabezado
    
    # Procesar TODAS las líneas, no solo las de la tabla
    for i, linea in enumerate(lineas):
        linea = linea.strip()
        
        # Detectar inicio de tabla de productos
        if not encontrado_tabla:
            # Buscar palabras clave que indican inicio de tabla
            if re.search(r"(codigo|descripcion|precio|cantidad|grado|um|alcoh|item|producto)", linea, re.IGNORECASE):
                encontrado_tabla = True
                en_seccion_productos = True
                skip_next = True  # Saltar la línea de encabezado
                continue
        
        if skip_next:
            skip_next = False
            continue
        
        # Detectar fin de tabla (totales, subtotales, etc.)
        if en_seccion_productos:
            if re.search(r"(subtotal|total\s+factura|neto|iva\s+\d+|total\s*:)", linea, re.IGNORECASE):
                if re.search(r"\d{1,3}(?:\.\d{3})+", linea):  # Tiene números grandes
                    en_seccion_productos = False
                    # NO salir, seguir procesando por si hay más items
        
        # Si encontramos tabla, procesar solo esa sección
        # Si NO encontramos tabla, procesar TODO el texto
        if encontrado_tabla and not en_seccion_productos:
            # Ya pasamos la sección de productos, pero seguimos buscando
            pass
        
        # Limpiar línea de caracteres problemáticos pero mantener estructura
        linea_limpia = re.sub(r'[^\w\s\.\,\d\-\$]', ' ', linea)
        linea_limpia = re.sub(r'\s+', ' ', linea_limpia).strip()
        
        if len(linea_limpia) < 8:  # Líneas muy cortas probablemente no son productos
                continue
            
        # Filtrar líneas que claramente NO son productos
        # Filtrar líneas que empiezan con palabras de encabezado/cliente
        if re.match(r"^(cliente|proveedor|rut|direccion|telefono|email|fecha|factura|boleta|razon\s+social)", linea_limpia, re.IGNORECASE):
                    continue
        
        # Filtrar líneas que contienen estas palabras clave (excepto si tienen código de producto al inicio)
        if re.search(r"(factura|boleta|rut|direccion|telefono|email|fecha|total|subtotal|iva|neto|proveedor|cliente)", linea_limpia, re.IGNORECASE):
            # Si tiene estas palabras pero NO tiene precio grande Y NO empieza con código, probablemente no es producto
            if not re.search(r"\d{4,}", linea_limpia) and not re.match(r"^\d{4,}", linea_limpia):
                continue
            
        try:
            # MÉTODO 1: Líneas que comienzan con código de producto (4-7 dígitos)
            match_codigo = re.match(r"^(\d{4,7})\s+(.+)", linea_limpia)
            
            if match_codigo:
                codigo = match_codigo.group(1)
                resto_linea = match_codigo.group(2)
                
                # Buscar precios con formato chileno: 19.000,00 o 19.000 o 19000
                # Patrón más flexible
                precios = re.findall(r"(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d{4,})", resto_linea)
                
                if precios:
                    # Filtrar y convertir precios
                    precios_numericos = []
                    for p in precios:
                        try:
                            # Limpiar y convertir precio
                            precio_limpio = p.replace(".", "").replace(",", ".")
                            precio_num = float(precio_limpio)
                            # Precios razonables: entre 1.000 y 10.000.000
                            if 1000 <= precio_num <= 10000000:
                                precios_numericos.append(int(precio_num))
                        except:
                            continue
                    
                    if precios_numericos:
                        # Tomar el precio más grande que no sea extremo (probablemente precio unitario)
                        precios_ordenados = sorted(precios_numericos, reverse=True)
                        # Filtrar precios extremos (probablemente totales)
                        precio = precios_ordenados[0]
                        if len(precios_ordenados) > 1 and precios_ordenados[0] > precios_ordenados[1] * 10:
                            precio = precios_ordenados[1]  # Tomar el segundo si el primero es muy grande
                        
                        # Buscar cantidad (número pequeño, generalmente 1-100)
                        # La cantidad generalmente está después del nombre y antes del precio
                        cantidad = 1
                        
                        # Buscar números pequeños que podrían ser cantidad
                        # Pero excluir números que son parte de códigos (más de 3 dígitos seguidos)
                        numeros_pequenos = re.findall(r"\b([1-9]\d{0,2})\b", resto_linea)
                        
                        # Filtrar números que parecen ser parte de códigos o nombres
                        cantidades_validas = []
                        for num_str in numeros_pequenos:
                            try:
                                num = int(num_str)
                                # Cantidades razonables: entre 1 y 100 (raro tener más de 100 unidades)
                                if 1 <= num <= 100:
                                    # Verificar que no esté dentro de un código más largo
                                    idx = resto_linea.find(num_str)
                                    if idx > 0:
                                        # Verificar contexto: no debe estar rodeado de más dígitos
                                        antes = resto_linea[max(0, idx-1):idx]
                                        despues = resto_linea[idx+len(num_str):idx+len(num_str)+1]
                                        if not (antes.isdigit() or despues.isdigit()):
                                            cantidades_validas.append(num)
                            except:
                                pass
                        
                        if cantidades_validas:
                            # Tomar la cantidad más pequeña (probablemente la correcta)
                            cantidad = min(cantidades_validas)
                        
                        # Extraer nombre del producto (más inteligente)
                        nombre = resto_linea
                        
                        # Quitar códigos al inicio si quedaron
                        nombre = re.sub(r"^\d{4,7}\s*", "", nombre)
                        
                        # Quitar códigos alfanuméricos al inicio (ej: "a47065", "SI 245856")
                        nombre = re.sub(r"^[A-Za-z]?\s*\d{4,7}\s+", "", nombre)
                        nombre = re.sub(r"^[A-Z]{1,3}\s+\d{4,7}\s+", "", nombre)
                        
                        # Quitar grados alcohólicos (43,0, 12,0, etc.) - formato decimal con coma
                        nombre = re.sub(r"\b\d{1,2}[,\.]\d\b", "", nombre)
                        
                        # Quitar precios (todos los números grandes)
                        for p in precios:
                            nombre = nombre.replace(p, " ")
                        
                        # Quitar cantidades detectadas
                        if cantidad > 1:
                            nombre = nombre.replace(str(cantidad), " ", 1)  # Solo la primera ocurrencia
                        
                        # Quitar unidades de medida comunes
                        nombre = re.sub(r"\b(CJ|UN|KG|LT|PZ|UM|GL|ML|CL)\b", "", nombre, flags=re.IGNORECASE)
                        
                        # Quitar porcentajes (41,66, 43,29, etc.)
                        nombre = re.sub(r"\b\d{1,2}[,\.]\d{1,2}\s*%", "", nombre)
                        
                        # Quitar números grandes que quedaron (probablemente códigos mezclados)
                        nombre = re.sub(r"\b\d{3,}\b", "", nombre)
                        
                        # Quitar números pequeños sueltos al final (probablemente cantidades residuales)
                        nombre = re.sub(r"\s+\d{1,2}\s*$", "", nombre)
                        
                        # Limpiar caracteres raros y espacios múltiples
                        nombre = re.sub(r'[^\w\s]', ' ', nombre)  # Reemplazar caracteres raros con espacio
                        nombre = re.sub(r'\s+', ' ', nombre).strip()
                        nombre = re.sub(r'^[^\w]+|[^\w]+$', '', nombre)  # Quitar caracteres no alfanuméricos al inicio/fin
                        
                        # Limpiar palabras sueltas de una letra (errores de OCR)
                        palabras = nombre.split()
                        palabras_limpias = []
                        for palabra in palabras:
                            # Mantener palabras de 2+ letras, o palabras de 1 letra si son comunes (a, y, etc.)
                            if len(palabra) >= 2 or palabra.lower() in ['a', 'y', 'o', 'e', 'i', 'u']:
                                palabras_limpias.append(palabra)
                        nombre = ' '.join(palabras_limpias)
                        
                        # Validar que el nombre tenga sentido
                        if len(nombre) >= 3 and not nombre.isdigit():
                            # Verificar que tenga al menos una letra
                            if re.search(r'[a-zA-ZÁÉÍÓÚáéíóúÑñ]', nombre):
                                # Filtrar nombres que son claramente información del cliente/proveedor
                                if not re.search(r"^(cliente|proveedor|rut|direccion|telefono|email|fecha|andrea|alejandra|canto)", nombre, re.IGNORECASE):
                                    items.append({
                                        "nombre": nombre,
                                        "cantidad": cantidad,
                                        "precio": precio
                                    })
                                    continue
            
            # MÉTODO 2: Buscar líneas con precios grandes sin código al inicio
            # (para facturas con formato diferente o cuando el código no se detectó)
            precios = re.findall(r"(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d{4,})", linea_limpia)
            if precios and len(linea_limpia) > 15:
                precios_numericos = []
                for p in precios:
                    try:
                        precio_limpio = p.replace(".", "").replace(",", ".")
                        precio_num = float(precio_limpio)
                        if 1000 <= precio_num <= 10000000:
                            precios_numericos.append(int(precio_num))
                    except:
                        continue
                
                if precios_numericos:
                    precio = max(precios_numericos)
                    
                    # Buscar cantidad
                    cantidad = 1
                    cantidad_match = re.search(r"\b([1-9]\d{0,2})\b", linea_limpia)
                    if cantidad_match:
                        try:
                            cant = int(cantidad_match.group(1))
                            if 1 <= cant <= 1000:
                                cantidad = cant
                        except:
                            pass
                    
                    # Extraer nombre (todo antes del primer precio grande)
                    nombre = linea_limpia
                    # Encontrar posición del primer precio grande
                    for p in precios:
                        try:
                            precio_limpio = p.replace(".", "").replace(",", ".")
                            precio_num = float(precio_limpio)
                            if 1000 <= precio_num <= 10000000:
                                idx = nombre.find(p)
                                if idx > 5:  # Asegurar que hay texto antes
                                    nombre = nombre[:idx].strip()
                                    break
                        except:
                            continue
                    
                    # Limpiar nombre
                    nombre = re.sub(r"^\d{4,7}\s*", "", nombre)
                    nombre = re.sub(r'\s+', ' ', nombre).strip()
                    
                    # Validar nombre
                    if len(nombre) >= 3 and not nombre.isdigit():
                        if re.search(r'[a-zA-ZÁÉÍÓÚáéíóúÑñ]', nombre):
                            items.append({
                                "nombre": nombre,
                                "cantidad": cantidad,
                                "precio": precio
                            })

        except Exception as e:
            # Continuar con la siguiente línea si hay error
            continue

    return items
