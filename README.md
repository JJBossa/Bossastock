# STOCKEX - Sistema de Gestión de Inventario

Sistema completo de gestión de inventario desarrollado con Django 5.2.8. Permite gestionar productos, ventas, clientes, almacenes, compras y mucho más.

## 📋 Tabla de Contenidos
- [Características](#características)
- [Instalación](#instalación)
- [Uso](#uso)
- [Documentación](#documentación)
- [Testing](#testing)
- [Seguridad](#seguridad)
- [Despliegue](#despliegue)

## Características

### Funcionalidades Principales
- ✅ Sistema de autenticación (login/logout) con gestión de usuarios
- ✅ Visualización de productos con diseño moderno y responsive
- ✅ **Imágenes de productos** - Cada producto puede tener su imagen (con optimización automática)
- ✅ Búsqueda avanzada de productos (nombre, SKU, descripción)
- ✅ **Búsqueda rápida por código de barras** - Presiona `F` para acceso rápido
- ✅ Filtros avanzados (categoría, precio, stock, fecha)
- ✅ Paginación de resultados
- ✅ Indicadores visuales de stock (verde/amarillo/rojo)
- ✅ **Productos favoritos** - Marca tus productos más usados
- ✅ **Modo oscuro/claro** - Interfaz adaptable con preferencia guardada
- ✅ Dashboard con estadísticas completas
- ✅ Historial de cambios y auditoría completa

### Sistema de Facturas
- ✅ **Sistema de Facturas con OCR** - Sube facturas y actualiza stock automáticamente
- ✅ Detección automática de productos en facturas
- ✅ Procesamiento inteligente de texto con Tesseract OCR
- ✅ Gestión de proveedores

### Exportación y Reportes
- ✅ Exportar a PDF/Excel/CSV
- ✅ Estadísticas detalladas en dashboard

### Gestión y Administración
- ✅ Categorías de productos con colores personalizables
- ✅ Gestión completa de usuarios (crear, editar, resetear contraseñas)
- ✅ Panel de administración completo (Django Admin)
- ✅ Script de inicio automático (`iniciar.bat`) - Funciona desde cualquier ubicación

## Instalación

1. Asegúrate de tener Python 3.8+ instalado

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. **Instala Tesseract OCR** (requerido para procesar facturas):
   - Windows: Descarga desde https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `sudo apt install tesseract-ocr tesseract-ocr-spa`
   - macOS: `brew install tesseract tesseract-lang`
   
   Ver instrucciones detalladas en `INSTALACION_TESSERACT.md`

4. Realiza las migraciones:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Crea un superusuario (para acceder al admin y hacer login):
```bash
python manage.py createsuperuser
```

6. Importa los productos desde el PDF:
```bash
python manage.py importar_productos
```

7. Crea las categorías iniciales:
```bash
python manage.py crear_categorias
```

8. Inicia el servidor de desarrollo:
```bash
python manage.py runserver
```

9. Accede a la aplicación:
   - Login: http://127.0.0.1:8000/login/
   - Admin: http://127.0.0.1:8000/admin/

## Uso

### Gestión de Productos

1. Inicia sesión con las credenciales del superusuario creado
2. En la página principal verás todos los productos
3. Usa la barra de búsqueda para filtrar por nombre, SKU o descripción
4. Selecciona filtros avanzados (categoría, precio, stock)
5. Los productos se muestran en tarjetas con información de precio y stock

### Sistema de Facturas

1. Como admin, ve a "Facturas" desde el menú
2. Haz clic en "Subir Factura"
3. Selecciona un archivo PDF o imagen de la factura
4. El sistema procesará automáticamente la factura usando OCR
5. Revisa y corrige los items detectados si es necesario
6. Asigna productos a los items que no coincidieron automáticamente
7. Confirma la factura para actualizar el stock automáticamente

### Agregar Imágenes a los Productos

1. Accede al panel de administración: http://127.0.0.1:8000/admin/
2. Ve a "Productos" y selecciona el producto que deseas editar
3. En el campo "Imagen del Producto", haz clic en "Elegir archivo" y selecciona una imagen
4. Guarda los cambios
5. La imagen aparecerá automáticamente en la página principal

**Nota:** Si un producto no tiene imagen, se mostrará un placeholder con un icono.

## Estructura del Proyecto

```
proyecto_boti/
├── control_stock/          # Configuración del proyecto
├── inventario/            # Aplicación principal
│   ├── models.py          # Modelo Producto
│   ├── views.py           # Vistas (login, inicio)
│   ├── urls.py            # URLs de la app
│   └── management/        # Comandos personalizados
├── templates/             # Templates HTML
│   ├── base.html
│   └── inventario/
│       ├── login.html
│       └── inicio.html
├── static/                # Archivos estáticos
├── media/                 # Archivos subidos (imágenes de productos)
│   └── productos/         # Imágenes de productos
└── manage.py
```

## Modelo de Datos

**Producto:**
- nombre: CharField (máx. 200 caracteres)
- precio: DecimalField
- stock: IntegerField
- imagen: ImageField (opcional) - Imagen del producto
- fecha_creacion: DateTimeField
- fecha_actualizacion: DateTimeField

## Personalización

Puedes modificar los productos desde:
- El panel de administración de Django (`/admin/`)
- El comando `importar_productos.py` para agregar más productos

## 📚 Documentación

- **[Guía de Usuario](GUIA_USUARIO.md)** - Manual completo para usuarios
- **[Documentación Técnica](DOCUMENTACION_TECNICA.md)** - Detalles técnicos del sistema
- **[API Documentation](API_DOCUMENTATION.md)** - Documentación de la API REST

## 🧪 Testing

El proyecto incluye tests automatizados usando pytest:

```bash
# Ejecutar todos los tests
pytest

# Con cobertura de código
pytest --cov=. --cov-report=html

# Tests específicos
pytest tests/test_models.py
pytest tests/test_views.py
```

### Estructura de Tests
- `tests/test_models.py` - Tests de modelos básicos
- `tests/test_views.py` - Tests de vistas básicas
- `tests/test_models_extended.py` - Tests extendidos de modelos
- `tests/test_views_extended.py` - Tests extendidos de vistas
- `tests/factories.py` - Factories para datos de prueba
- `tests/conftest.py` - Fixtures globales

## 🔒 Seguridad

### Configuración Automática
El sistema detecta automáticamente si está en desarrollo o producción:

- **Desarrollo Local (DEBUG=True)**: Configuraciones relajadas para facilitar el uso
- **Producción (DEBUG=False)**: Configuraciones estrictas de seguridad

### Variables de Entorno Recomendadas para Producción
```bash
SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
SECURE_HSTS_SECONDS=31536000
SECURE_SSL_REDIRECT=True
```

**Nota:** En desarrollo local, no necesitas configurar estas variables. El sistema funciona perfectamente sin ellas.

## 🚀 Despliegue

### Requisitos
- Python 3.8+
- PostgreSQL (producción) o SQLite (desarrollo)
- Servidor web (Nginx/Apache) + Gunicorn

### Pasos Rápidos
1. Configurar variables de entorno (solo producción)
2. `pip install -r requirements.txt`
3. `python manage.py migrate`
4. `python manage.py collectstatic`
5. Iniciar con Gunicorn

Ver [Documentación Técnica](DOCUMENTACION_TECNICA.md) para detalles completos.

## 🛠️ Tecnologías Utilizadas

- **Backend**: Django 5.2.8
- **Frontend**: Bootstrap 5.3.0, Bootstrap Icons
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **API**: Django REST Framework
- **Autenticación**: JWT + Session Authentication
- **OCR**: Tesseract (procesamiento de facturas)
- **Exportación**: ReportLab (PDF), OpenPyXL (Excel)
- **Testing**: pytest, pytest-django, factory-boy

## 📝 Licencia

Este proyecto es de uso privado. Todos los derechos reservados.

## 👤 Autor

Juan Jose Bossa Canto

---

**¿Necesitas ayuda?** Consulta la [Guía de Usuario](GUIA_USUARIO.md) o la [Documentación Técnica](DOCUMENTACION_TECNICA.md).

