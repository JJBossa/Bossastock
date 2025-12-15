"""
Utilidades para procesamiento OCR de facturas
"""
import pytesseract
from PIL import Image
import re
from pdf2image import convert_from_path
import io
from django.conf import settings
import os

# Configurar ruta de Tesseract si es necesario (Windows)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def procesar_imagen_ocr(archivo):
    """
    Procesa una imagen o PDF y extrae texto usando OCR
    
    Args:
        archivo: Archivo subido (imagen o PDF)
    
    Returns:
        str: Texto extraído
    """
    try:
        # Si es PDF, convertir a imagen
        if archivo.name.lower().endswith('.pdf'):
            # Guardar temporalmente el PDF
            temp_path = os.path.join(settings.MEDIA_ROOT, 'temp', archivo.name)
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            archivo.seek(0)  # Volver al inicio
            with open(temp_path, 'wb') as f:
                for chunk in archivo.chunks():
                    f.write(chunk)
            
            # Convertir PDF a imágenes
            images = convert_from_path(temp_path, dpi=300)
            
            # Extraer texto de todas las páginas
            texto_completo = []
            for img in images:
                # Configurar OCR con mejor precisión
                texto = pytesseract.image_to_string(img, lang='spa', config='--psm 6')
                texto_completo.append(texto)
            
            # Limpiar archivo temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return '\n'.join(texto_completo)
        
        # Si es imagen, procesar directamente
        else:
            archivo.seek(0)  # Volver al inicio del archivo
            imagen = Image.open(archivo)
            # Configurar OCR con mejor precisión para imágenes
            texto = pytesseract.image_to_string(imagen, lang='spa', config='--psm 6')
            return texto
    
    except Exception as e:
        print(f"Error en OCR: {str(e)}")
        return ""

def extraer_fecha(texto):
    """Extrae fecha del texto de la factura"""
    # Patrones comunes de fecha
    patrones = [
        r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})',  # DD/MM/YYYY o DD-MM-YYYY
        r'(\d{2,4})[\/\-](\d{1,2})[\/\-](\d{1,2})',  # YYYY/MM/DD
    ]
    
    for patron in patrones:
        match = re.search(patron, texto)
        if match:
            try:
                from datetime import datetime
                fecha_str = match.group(0).replace('-', '/')
                # Intentar parsear
                for fmt in ['%d/%m/%Y', '%Y/%m/%d', '%d/%m/%y']:
                    try:
                        return datetime.strptime(fecha_str, fmt).date()
                    except:
                        continue
            except:
                continue
    
    return None

def extraer_numero_factura(texto):
    """Extrae número de factura del texto"""
    # Buscar patrones como "Factura N° 12345" o "N°: 12345"
    patrones = [
        r'[Ff]actura\s*[Nn]°?\s*:?\s*(\d+)',
        r'[Nn]°?\s*:?\s*(\d{4,})',
        r'[Ff]actura\s*#?\s*:?\s*(\d+)',
    ]
    
    for patron in patrones:
        match = re.search(patron, texto)
        if match:
            return match.group(1)
    
    return None

def extraer_total(texto):
    """Extrae el total de la factura"""
    # Buscar patrones como "Total: $12345" o "TOTAL 12345"
    patrones = [
        r'[Tt]otal\s*:?\s*\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d+)?)',
        r'[Tt]otal\s*:?\s*(\d{1,3}(?:\.\d{3})*(?:,\d+)?)',
    ]
    
    for patron in patrones:
        match = re.search(patron, texto)
        if match:
            total_str = match.group(1).replace('.', '').replace(',', '')
            try:
                return int(total_str)
            except:
                continue
    
    return None

def extraer_items_factura(texto, productos_existentes):
    """
    Extrae items de la factura intentando coincidir con productos existentes
    
    Args:
        texto: Texto extraído de la factura
        productos_existentes: QuerySet de productos existentes
    
    Returns:
        list: Lista de diccionarios con items detectados
    """
    items = []
    lineas = texto.split('\n')
    
    # Crear diccionario de productos para búsqueda rápida
    productos_dict = {}
    for producto in productos_existentes:
        nombre_limpio = producto.nombre.lower().strip()
        productos_dict[nombre_limpio] = producto
        # También agregar variaciones (palabras clave)
        palabras = nombre_limpio.split()
        for palabra in palabras:
            if len(palabra) > 3:  # Solo palabras significativas
                productos_dict[palabra] = producto
    
    # Patrones más flexibles para detectar items
    # Buscar líneas que contengan números grandes (precios) y texto (nombres)
    
    for i, linea in enumerate(lineas):
        linea = linea.strip()
        if not linea or len(linea) < 5:
            continue
        
        # Limpiar línea de caracteres especiales problemáticos
        linea_limpia = re.sub(r'[^\w\s\.\,\$\-]', ' ', linea)
        
        # Buscar números grandes que podrían ser precios (más de 3 dígitos)
        numeros_grandes = re.findall(r'\d{1,3}(?:\.\d{3})*(?:,\d+)?', linea_limpia)
        
        if len(numeros_grandes) >= 1:
            # Intentar extraer información
            partes = linea_limpia.split()
            
            # Buscar cantidad (número pequeño, generalmente al inicio o después del nombre)
            cantidad = 1
            cantidad_encontrada = False
            
            # Buscar números que podrían ser cantidades (1-1000)
            for parte in partes:
                if parte.isdigit() and 1 <= int(parte) <= 1000:
                    cantidad = int(parte)
                    cantidad_encontrada = True
                    break
            
            # Extraer precio (último número grande o penúltimo)
            precio = None
            if numeros_grandes:
                # Tomar el último número grande como precio
                precio_str = numeros_grandes[-1].replace('.', '').replace(',', '')
                try:
                    precio = int(precio_str)
                except:
                    pass
            
            # Si no hay precio válido, saltar esta línea
            if not precio or precio < 100:  # Precios muy bajos probablemente no son válidos
                continue
            
            # Extraer nombre del producto (todo antes de los números grandes)
            # Buscar donde empiezan los números
            nombre_partes = []
            for parte in partes:
                # Si encontramos un número grande, paramos
                if re.match(r'\d{1,3}(?:\.\d{3})*(?:,\d+)?', parte):
                    break
                # Si es un número pequeño y ya tenemos nombre, podría ser cantidad
                if parte.isdigit() and len(nombre_partes) > 0:
                    continue
                nombre_partes.append(parte)
            
            nombre = ' '.join(nombre_partes).strip()
            
            # Limpiar nombre de palabras comunes que no son parte del producto
            palabras_excluir = ['codigo', 'cod', 'descripcion', 'um', 'cantidad', 'precio', 'unit', 
                               'descuento', 'valor', 'ptax', 'unidad', 'código', 'descripción']
            nombre_palabras = nombre.split()
            nombre_limpio = ' '.join([p for p in nombre_palabras if p.lower() not in palabras_excluir])
            
            if len(nombre_limpio) < 3:  # Nombre muy corto, probablemente no es válido
                continue
            
            # Calcular subtotal
            subtotal = precio * cantidad
            
            # Intentar encontrar producto coincidente
            producto_coincidencia = None
            nombre_lower = nombre_limpio.lower().strip()
            
            # Búsqueda exacta
            if nombre_lower in productos_dict:
                producto_coincidencia = productos_dict[nombre_lower]
            else:
                # Búsqueda parcial - buscar palabras clave del nombre en productos
                palabras_nombre = nombre_lower.split()
                mejor_coincidencia = None
                mejor_score = 0
                
                for prod_nombre, producto in productos_dict.items():
                    score = 0
                    # Contar palabras que coinciden
                    for palabra in palabras_nombre:
                        if len(palabra) > 3 and palabra in prod_nombre:
                            score += 1
                        if prod_nombre in palabra:
                            score += 2
                    
                    if score > mejor_score:
                        mejor_score = score
                        mejor_coincidencia = producto
                
                if mejor_score >= 1:  # Al menos una palabra coincide
                    producto_coincidencia = mejor_coincidencia
            
            items.append({
                'nombre_producto': nombre_limpio,
                'cantidad': cantidad,
                'precio_unitario': precio,
                'subtotal': subtotal,
                'producto': producto_coincidencia,
                'producto_coincidencia': producto_coincidencia is not None
            })
    
    # Si no se encontraron items con el método anterior, intentar método más simple
    if len(items) == 0:
        # Buscar líneas con formato: texto + número grande
        for linea in lineas:
            linea = linea.strip()
            if len(linea) < 10:
                continue
            
            # Buscar cualquier número grande (precio) - formato chileno con puntos
            match_precio = re.search(r'(\d{1,3}(?:\.\d{3})*(?:,\d+)?)', linea)
            if match_precio:
                precio_str = match_precio.group(1).replace('.', '').replace(',', '')
                try:
                    precio = int(precio_str)
                    if precio >= 1000:  # Solo precios razonables
                        # Todo antes del precio es el nombre
                        nombre = linea[:match_precio.start()].strip()
                        # Limpiar nombre
                        nombre = re.sub(r'^\d+\s*', '', nombre)  # Quitar códigos al inicio
                        nombre = nombre.strip()
                        
                        if len(nombre) > 3:
                            # Buscar producto
                            producto_coincidencia = None
                            nombre_lower = nombre.lower()
                            for prod_nombre, producto in productos_dict.items():
                                if prod_nombre in nombre_lower or nombre_lower in prod_nombre:
                                    producto_coincidencia = producto
                                    break
                            
                            items.append({
                                'nombre_producto': nombre,
                                'cantidad': 1,
                                'precio_unitario': precio,
                                'subtotal': precio,
                                'producto': producto_coincidencia,
                                'producto_coincidencia': producto_coincidencia is not None
                            })
                except:
                    continue
    
    # Método adicional: buscar patrones de tabla (formato factura chilena)
    # Formato típico: código descripción cantidad precio_unitario subtotal
    if len(items) == 0:
        # Buscar líneas que tengan múltiples números separados (formato tabla)
        for i, linea in enumerate(lineas):
            linea = linea.strip()
            if len(linea) < 15:
                continue
            
            # Buscar múltiples números grandes separados (columnas de tabla)
            numeros = re.findall(r'\d{1,3}(?:\.\d{3})*(?:,\d+)?', linea)
            
            if len(numeros) >= 2:  # Al menos cantidad y precio
                # El último número suele ser el subtotal o precio unitario
                # El penúltimo podría ser precio unitario
                # Buscar cantidad (número pequeño, generalmente 1-100)
                cantidad = 1
                precio = None
                
                # Intentar identificar cantidad y precio
                for num_str in numeros:
                    num_limpio = num_str.replace('.', '').replace(',', '')
                    try:
                        num_val = int(num_limpio)
                        # Si es un número pequeño, probablemente es cantidad
                        if 1 <= num_val <= 100:
                            cantidad = num_val
                        # Si es un número grande (>= 1000), probablemente es precio
                        elif num_val >= 1000 and precio is None:
                            precio = num_val
                    except:
                        continue
                
                if precio and precio >= 1000:
                    # Extraer nombre (todo antes de los números)
                    # Buscar donde empieza el primer número
                    match_primero = re.search(r'\d', linea)
                    if match_primero:
                        nombre = linea[:match_primero.start()].strip()
                        # Limpiar nombre
                        nombre = re.sub(r'^\d+\s*', '', nombre)  # Quitar códigos
                        nombre = re.sub(r'\s+', ' ', nombre)  # Normalizar espacios
                        nombre = nombre.strip()
                        
                        # Excluir palabras comunes de encabezados
                        palabras_excluir = ['codigo', 'cod', 'descripcion', 'um', 'cantidad', 
                                           'precio', 'unit', 'descuento', 'valor', 'ptax', 
                                           'unidad', 'código', 'descripción', 'alcoh']
                        nombre_palabras = nombre.split()
                        nombre_limpio = ' '.join([p for p in nombre_palabras 
                                                 if p.lower() not in palabras_excluir])
                        
                        if len(nombre_limpio) >= 3:
                            # Buscar producto
                            producto_coincidencia = None
                            nombre_lower = nombre_limpio.lower()
                            for prod_nombre, producto in productos_dict.items():
                                if prod_nombre in nombre_lower or nombre_lower in prod_nombre:
                                    producto_coincidencia = producto
                                    break
                            
                            items.append({
                                'nombre_producto': nombre_limpio,
                                'cantidad': cantidad,
                                'precio_unitario': precio,
                                'subtotal': precio * cantidad,
                                'producto': producto_coincidencia,
                                'producto_coincidencia': producto_coincidencia is not None
                            })
    
    return items

