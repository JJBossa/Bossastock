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

# Idioma a usar para OCR (español)
OCR_LANG = "spa"


def procesar_imagen_ocr(img, usar_color=False):
    """
    Procesa una imagen (PIL o numpy array) con OCR.
    Optimizado para velocidad manteniendo precisión.
    Usa estrategia de "early exit" - se detiene cuando encuentra un buen resultado.
    
    Args:
        img: Imagen PIL o numpy array
        usar_color: Si True, intenta procesar en color (mejor para algunas facturas)
    
    Returns:
        str: Texto extraído
    """
    textos = []
    
    # Reducir tamaño de imagen si es muy grande (acelera OCR significativamente)
    # OCR funciona bien con 150-200 DPI, no necesitamos más
    if isinstance(img, Image.Image):
        max_width = 2000  # Ancho máximo recomendado
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
    
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
    
    # Estrategia 1: Procesar en color (solo si se solicita explícitamente)
    # Solo probar el mejor modo PSM para velocidad
    if usar_color and CV2_AVAILABLE and img_cv is not None:
        try:
            texto = pytesseract.image_to_string(
                img_cv,
                lang=OCR_LANG,
                config=f"--psm 6 --oem 3"  # PSM 6 es mejor para tablas
            )
            if texto.strip() and len(texto.strip()) > 50:
                textos.append(texto)
        except:
            pass
    
    # Estrategia 2: Preprocesamiento optimizado (solo las mejores estrategias)
    # Early exit: si obtenemos un buen resultado, no probamos todas las combinaciones
    if CV2_AVAILABLE and img_cv is not None:
        try:
            # Convertir a gris
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Solo las 2 mejores variantes de imagen (las más efectivas)
            try:
                clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8))
                gray_contrast = clahe.apply(gray)
            except:
                gray_contrast = cv2.equalizeHist(gray)
            
            # Solo las 3 mejores estrategias de binarización (las más efectivas)
            estrategias_optimizadas = [
                # 1. Binarización adaptativa (mejor para documentos escaneados) - MEJOR
                lambda g: cv2.adaptiveThreshold(
                    g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                ),
                # 2. Otsu threshold (automático) - SEGUNDA MEJOR
                lambda g: cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
                # 3. Sin binarizar (para algunas imágenes) - TERCERA
                lambda g: g,
            ]
            
            # Solo 2 variantes de imagen (las mejores)
            imagenes_variantes_optimizadas = [
                ("contrast", gray_contrast),  # Mejor para contraste
                ("original", gray),  # Fallback
            ]
            
            # Solo 2 modos PSM (los más efectivos para tablas)
            psm_modes_optimizados = [6, 11]  # PSM 6 para tablas, PSM 11 como fallback
            
            # Probar todas las estrategias y recopilar todos los textos
            # (no hacer early exit para asegurar que probamos todas las mejores estrategias)
            for nombre_var, img_var in imagenes_variantes_optimizadas:
                for estrategia in estrategias_optimizadas:
                    try:
                        processed = estrategia(img_var)
                        
                        # Probar solo los mejores modos PSM
                        for psm_mode in psm_modes_optimizados:
                            try:
                                texto = pytesseract.image_to_string(
                                    processed,
                                    lang=OCR_LANG,
                                    config=f"--psm {psm_mode} --oem 3"
                                )
                                if texto.strip() and len(texto.strip()) > 50:
                                    textos.append(texto)
                            except:
                                continue
                    except:
                        continue
                
        except Exception as e:
            print(f"Error en preprocesamiento OpenCV: {str(e)}")
    
    # Estrategia 3: PIL (fallback) - Solo si no tenemos resultados buenos
    if not textos and isinstance(img, Image.Image):
        try:
            # Solo probar con imagen original y el mejor modo PSM
            try:
                texto = pytesseract.image_to_string(
                    img,
                    lang=OCR_LANG,
                    config=f"--psm 6 --oem 3"  # PSM 6 es el mejor para tablas
                )
                if texto.strip() and len(texto.strip()) > 50:
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
            # Solo marcar fin si es claramente un total (número muy grande)
            if re.search(r"(subtotal|total\s+factura|neto|iva\s+\d+|total\s*:)", linea, re.IGNORECASE):
                numeros = re.findall(r"(\d{1,3}(?:\.\d{3})+)", linea)
                if numeros:
                    # Si hay un número muy grande (más de 50.000), probablemente es un total
                    for num_str in numeros:
                        try:
                            num = int(num_str.replace(".", ""))
                            if num > 50000:  # Números muy grandes son totales
                                en_seccion_productos = False
                                break
                        except:
                            pass
        
        # Si encontramos tabla, procesar solo esa sección
        # Si NO encontramos tabla, procesar TODO el texto
        if encontrado_tabla and not en_seccion_productos:
            # Ya pasamos la sección de productos, pero seguimos buscando
            pass
        
        # Limpiar línea de caracteres problemáticos pero mantener estructura
        linea_limpia = re.sub(r'[^\w\s\.\,\d\-\$]', ' ', linea)
        linea_limpia = re.sub(r'\s+', ' ', linea_limpia).strip()
        
        if len(linea_limpia) < 6:  # Líneas muy cortas probablemente no son productos
            continue
        
        # Filtrar líneas que claramente NO son productos (solo si NO empiezan con código)
        # Si empieza con código de producto, procesarla de todas formas
        if not re.match(r"^\d{4,}", linea_limpia):
            # Filtrar líneas que empiezan con palabras de encabezado/cliente
            if re.match(r"^(cliente|proveedor|rut|direccion|telefono|email|fecha|factura|boleta|razon\s+social|pisquera)", linea_limpia, re.IGNORECASE):
                continue
            
            # Filtrar líneas que contienen estas palabras clave Y NO tienen código ni precio
            if re.search(r"(factura|boleta|rut|direccion|telefono|email|fecha|total|subtotal|iva|neto|proveedor|cliente|observaciones)", linea_limpia, re.IGNORECASE):
                # Si tiene estas palabras pero NO tiene precio grande Y NO empieza con código, probablemente no es producto
                if not re.search(r"\d{4,}", linea_limpia):
                    continue
            
        try:
            # MÉTODO 1: Líneas que comienzan con código de producto (6 dígitos es común en facturas chilenas)
            # Buscar códigos de 4-7 dígitos al inicio de la línea
            match_codigo = re.match(r"^(\d{4,7})\s+(.+)", linea_limpia)
            
            if match_codigo:
                codigo = match_codigo.group(1)
                resto_linea = match_codigo.group(2)
                
                # Buscar TODOS los números en la línea (precios, cantidades, descuentos, etc.)
                # Formato chileno: 19.000,00 o 19.000 o 19000
                # Capturar todos los números con formato chileno
                todos_numeros = re.findall(r"(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?|\d{4,})", resto_linea)
                
                if todos_numeros:
                    # Convertir todos los números a valores numéricos
                    numeros_procesados = []
                    for num_str in todos_numeros:
                        try:
                            # Limpiar y convertir (quitar puntos de miles, convertir coma a punto decimal)
                            num_limpio = num_str.replace(".", "").replace(",", ".")
                            num_valor = float(num_limpio)
                            numeros_procesados.append({
                                'valor': int(num_valor),
                                'original': num_str,
                                'posicion': resto_linea.find(num_str)
                            })
                        except:
                            continue
                    
                    if numeros_procesados:
                        # Separar por tipo de número
                        # CANTIDAD: números pequeños (1-1000), generalmente al inicio
                        # PRECIO UNITARIO: números medianos (1.000-100.000), generalmente el primero grande
                        # DESCUENTO: números medianos
                        # VALOR: números medianos (después del descuento)
                        # TOTAL: números grandes (más de 100.000)
                        
                        # Filtrar números que son cantidades (1-1000)
                        cantidades_candidatas = [n for n in numeros_procesados if 1 <= n['valor'] <= 1000]
                        
                        # Filtrar precios razonables (1.000-100.000 para precio unitario)
                        precios_candidatos = [n for n in numeros_procesados if 1000 <= n['valor'] <= 100000]
                        
                        # Si no hay precios en rango, ampliar un poco (algunos precios pueden ser menores)
                        if not precios_candidatos:
                            precios_candidatos = [n for n in numeros_procesados if 500 <= n['valor'] <= 200000]
                        
                        # Determinar cantidad (generalmente el número más pequeño al inicio, antes de la descripción larga)
                        cantidad = 1
                        if cantidades_candidatas:
                            # Tomar la cantidad más pequeña que esté en la primera mitad de la línea
                            mitad_linea = len(resto_linea) // 2
                            cantidades_iniciales = [c for c in cantidades_candidatas if c['posicion'] < mitad_linea]
                            if cantidades_iniciales:
                                cantidad = min(cantidades_iniciales, key=lambda x: (x['valor'], x['posicion']))['valor']
                            else:
                                cantidad = min(cantidades_candidatas, key=lambda x: x['valor'])['valor']
                        
                        # Determinar precio unitario
                        # En facturas chilenas, el precio unitario suele ser:
                        # - El primer precio grande que aparece (generalmente 10.000-100.000)
                        # - Antes de los descuentos y valores después de descuento
                        precio = None
                        if precios_candidatos:
                            # Ordenar por posición (el primero suele ser el precio unitario)
                            precios_ordenados = sorted(precios_candidatos, key=lambda x: x['posicion'])
                            
                            # El precio unitario generalmente es el más grande entre los primeros 2-3 precios
                            # (porque viene antes del descuento, y el valor después del descuento es menor)
                            primeros_precios = precios_ordenados[:3]
                            if primeros_precios:
                                # Tomar el precio más grande de los primeros (probablemente el unitario)
                                # porque generalmente: Precio Unit > Valor después descuento
                                precio_candidato = max(primeros_precios, key=lambda x: x['valor'])
                                
                                # Validar que sea razonable (generalmente entre 5.000 y 100.000)
                                if 5000 <= precio_candidato['valor'] <= 100000:
                                    precio = precio_candidato['valor']
                                elif precio_candidato['valor'] >= 1000:
                                    # Si está fuera del rango pero es razonable, usarlo igual
                                    precio = precio_candidato['valor']
                        
                        # Si no encontramos precio con la estrategia anterior, usar el primero
                        if not precio and precios_candidatos:
                            precios_ordenados = sorted(precios_candidatos, key=lambda x: x['posicion'])
                            if precios_ordenados:
                                precio = precios_ordenados[0]['valor']
                        
                        # Si todavía no hay precio, usar el más común o el más grande razonable
                        if not precio and precios_candidatos:
                            # Preferir el más grande de los primeros (para evitar valores después de descuento)
                            precios_ordenados = sorted(precios_candidatos, key=lambda x: x['posicion'])
                            primeros_3 = precios_ordenados[:3]
                            if primeros_3:
                                precio = max(primeros_3, key=lambda x: x['valor'])['valor']
                            else:
                                precio = max(precios_candidatos, key=lambda x: x['valor'])['valor']
                        
                        # Último recurso: usar cualquier número razonable
                        if not precio:
                            numeros_razonables = [n for n in numeros_procesados if 1000 <= n['valor'] <= 200000]
                            if numeros_razonables:
                                precio = max(numeros_razonables, key=lambda x: x['valor'])['valor']
                        
                        # Extraer nombre del producto (limpieza mejorada)
                        nombre = resto_linea
                        
                        # Paso 1: Quitar el código al inicio
                        nombre = re.sub(r"^\d{4,7}\s*", "", nombre)
                        nombre = re.sub(r"^[A-Za-z]?\s*\d{4,7}\s+", "", nombre)
                        nombre = re.sub(r"^[A-Z]{1,3}\s+\d{4,7}\s+", "", nombre)
                        
                        # Paso 2: Quitar todos los números de la línea (precios, cantidades, descuentos, etc.)
                        # Esto incluye: precios, grados alcohólicos, porcentajes, unidades de medida numéricas
                        for num_info in numeros_procesados:
                            # Quitar el número original de la línea
                            nombre = nombre.replace(num_info['original'], " ", 1)
                        
                        # Paso 3: Quitar grados alcohólicos (pueden quedar si no fueron números perfectos)
                        # Formato: 43,0 o 43.0 o 43 0
                        nombre = re.sub(r"\b\d{1,2}[,\.\s]\d\b", "", nombre)
                        
                        # Paso 4: Quitar unidades de medida comunes y códigos de formato
                        # CJ = Caja, UN = Unidad, VNR = Varios, LAT = Lata, etc.
                        nombre = re.sub(r"\b(CJ|UN|KG|LT|PZ|UM|GL|ML|CL|VNR|LAT|CC)\b", "", nombre, flags=re.IGNORECASE)
                        # Quitar formatos como "X6", "X12" (cantidad por unidad) - más agresivo
                        nombre = re.sub(r"\bX\d+\b", "", nombre, flags=re.IGNORECASE)
                        # Quitar "X" sueltas al final (residuales de "X6", "X12")
                        nombre = re.sub(r"\bX\b", "", nombre, flags=re.IGNORECASE)
                        # Quitar códigos como "CCX", "LAT473" que quedaron
                        nombre = re.sub(r"\b[A-Z]{2,3}\d+\b", "", nombre)
                        nombre = re.sub(r"\b\d+[A-Z]{2,3}\b", "", nombre)
                        
                        # Paso 5: Quitar porcentajes residuales
                        nombre = re.sub(r"\b\d{1,2}[,\.]\d{1,2}\s*%", "", nombre)
                        
                        # Paso 6: Quitar códigos alfanuméricos residuales (ej: "1000CCX6", "473X12")
                        nombre = re.sub(r"\b\d{3,}[A-Z]?[Xx]\d+\b", "", nombre)
                        nombre = re.sub(r"\b[A-Z]\d{3,}\b", "", nombre)
                        
                        # Paso 7: Limpiar espacios y caracteres raros
                        nombre = re.sub(r'[^\w\s\-\*]', ' ', nombre)  # Mantener guiones y asteriscos
                        nombre = re.sub(r'\s+', ' ', nombre).strip()
                        
                        # Paso 8: Quitar números residuales (cualquier número que quede)
                        palabras = nombre.split()
                        palabras_limpias = []
                        for palabra in palabras:
                            # Eliminar palabras que son solo números
                            if palabra.replace('.', '').replace(',', '').isdigit():
                                continue
                            # Mantener palabras con letras
                            if re.search(r'[a-zA-ZÁÉÍÓÚáéíóúÑñ]', palabra):
                                palabras_limpias.append(palabra)
                        
                        nombre = ' '.join(palabras_limpias)
                        
                        # Paso 9: Limpiar inicio y final
                        nombre = re.sub(r'^[^\w]+|[^\w]+$', '', nombre).strip()
                        
                        # Validar que el nombre tenga sentido
                        if len(nombre) >= 3 and not nombre.isdigit() and precio:
                            # Verificar que tenga al menos una letra
                            if re.search(r'[a-zA-ZÁÉÍÓÚáéíóúÑñ]', nombre):
                                # Filtrar nombres que son claramente información del cliente/proveedor
                                if not re.search(r"^(cliente|proveedor|rut|direccion|telefono|email|fecha|andrea|alejandra|canto|pisquera)", nombre, re.IGNORECASE):
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
