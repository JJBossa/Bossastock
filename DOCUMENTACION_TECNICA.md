# Documentación Técnica - STOCKEX

## Arquitectura del Sistema

### Stack Tecnológico
- **Backend**: Django 5.2.8
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Frontend**: Bootstrap 5.3.0, JavaScript vanilla
- **API**: Django REST Framework
- **Autenticación**: JWT + Session Authentication

### Estructura del Proyecto

```
proyecto_boti/
├── control_stock/          # Configuración del proyecto Django
│   ├── settings.py         # Configuraciones (seguridad, apps, etc.)
│   ├── urls.py             # URLs principales
│   └── wsgi.py             # WSGI para producción
├── inventario/             # Aplicación principal
│   ├── models.py           # Modelos de datos
│   ├── views.py            # Vistas principales
│   ├── views_*.py          # Vistas por módulo
│   ├── urls.py             # URLs de la aplicación
│   ├── api_views.py        # Vistas de API REST
│   ├── serializers.py      # Serializadores DRF
│   ├── forms.py            # Formularios
│   ├── utils.py            # Utilidades y helpers
│   └── management/         # Comandos personalizados
├── templates/              # Templates HTML
│   ├── base.html          # Template base
│   └── inventario/        # Templates de la app
├── static/                 # Archivos estáticos
│   ├── css/               # Hojas de estilo
│   └── js/                # Scripts JavaScript
├── media/                  # Archivos subidos
├── tests/                  # Tests automatizados
└── logs/                   # Logs del sistema
```

---

## Modelos de Datos

### Modelos Principales

#### Producto
- **Campos principales**: nombre, sku, precio, stock, categoria
- **Relaciones**: ForeignKey a Categoria
- **Propiedades**: stock_bajo, margen_ganancia, valor_inventario

#### Venta
- **Campos principales**: numero_venta, usuario, total, metodo_pago
- **Relaciones**: ForeignKey a Usuario, Cliente (opcional)
- **Relacionado**: ItemVenta (OneToMany)

#### Cliente
- **Campos principales**: nombre, rut, email, telefono
- **Relaciones**: OneToMany con Venta, CuentaPorCobrar

#### Almacen
- **Campos principales**: nombre, codigo, direccion
- **Relaciones**: OneToMany con StockAlmacen, Transferencia

#### Transferencia
- **Campos principales**: numero_transferencia, almacen_origen, almacen_destino
- **Relaciones**: ForeignKey a Almacen (origen y destino), Usuario
- **Relacionado**: ItemTransferencia (OneToMany)

#### OrdenCompra
- **Campos principales**: numero_orden, proveedor, estado
- **Relaciones**: ForeignKey a Proveedor
- **Relacionado**: ItemOrdenCompra (OneToMany)

---

## API REST

### Autenticación
- **Session Authentication**: Para uso web
- **JWT Authentication**: Para aplicaciones móviles/frontend separado

### Endpoints Principales

#### Productos
- `GET /api/v1/productos/` - Listar productos
- `POST /api/v1/productos/` - Crear producto
- `GET /api/v1/productos/{id}/` - Detalle de producto
- `PUT /api/v1/productos/{id}/` - Actualizar producto
- `DELETE /api/v1/productos/{id}/` - Eliminar producto

#### Ventas
- `GET /api/v1/ventas/` - Listar ventas
- `POST /api/v1/ventas/` - Crear venta
- `GET /api/v1/ventas/{id}/` - Detalle de venta

#### Clientes
- `GET /api/v1/clientes/` - Listar clientes
- `POST /api/v1/clientes/` - Crear cliente

### Filtrado y Búsqueda
Todos los endpoints soportan:
- **Filtrado**: `?campo=valor`
- **Búsqueda**: `?search=termino`
- **Ordenamiento**: `?ordering=campo` o `?ordering=-campo`
- **Paginación**: `?page=1`

---

## Seguridad

### Configuraciones de Seguridad

#### Desarrollo Local (DEBUG=True)
- `SESSION_COOKIE_SECURE = False` - Permite HTTP
- `CSRF_COOKIE_SECURE = False` - Permite HTTP
- `SECURE_SSL_REDIRECT = False` - No fuerza HTTPS

#### Producción (DEBUG=False)
- `SESSION_COOKIE_SECURE = True` - Solo HTTPS
- `CSRF_COOKIE_SECURE = True` - Solo HTTPS
- `SECURE_HSTS_SECONDS` - Configurable vía variable de entorno
- `X_FRAME_OPTIONS = 'DENY'` - Previene clickjacking

### Permisos
- **Administrador (bossa)**: Acceso completo
- **Usuarios normales**: Acceso limitado a funciones básicas
- **API**: Requiere autenticación (JWT o Session)

### Variables de Entorno Recomendadas
```bash
SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
SECURE_HSTS_SECONDS=31536000
SECURE_SSL_REDIRECT=True
```

---

## Optimizaciones

### Consultas a Base de Datos
- Uso de `select_related()` para ForeignKey
- Uso de `prefetch_related()` para ManyToMany
- Índices en campos frecuentemente consultados

### Caché
- **Desarrollo**: LocMemCache (memoria local)
- **Producción**: Redis recomendado

### Archivos Estáticos
- WhiteNoise para servir estáticos en producción
- Compresión automática de CSS/JS

---

## Testing

### Ejecutar Tests
```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=. --cov-report=html

# Tests específicos
pytest tests/test_models.py
pytest tests/test_views.py
```

### Estructura de Tests
- `tests/test_models.py` - Tests de modelos
- `tests/test_views.py` - Tests de vistas básicas
- `tests/test_views_extended.py` - Tests extendidos de vistas
- `tests/test_models_extended.py` - Tests extendidos de modelos
- `tests/factories.py` - Factories para datos de prueba
- `tests/conftest.py` - Fixtures globales

---

## Logging

### Configuración
Los logs se guardan en `logs/`:
- `inventario.log` - Logs generales
- `errors.log` - Solo errores

### Niveles de Log
- **INFO**: Operaciones normales
- **ERROR**: Errores del sistema
- **DEBUG**: Información detallada (solo en desarrollo)

---

## Comandos Personalizados

### Gestión de Usuarios
```bash
python manage.py crear_superusuario
python manage.py crear_usuario_normal
```

### Gestión de Datos
```bash
python manage.py crear_categorias
python manage.py importar_productos
python manage.py exportar_datos
```

### Limpieza
```bash
python manage.py eliminar_imagenes
```

---

## Despliegue

### Requisitos
- Python 3.8+
- PostgreSQL (producción)
- Servidor web (Nginx/Apache)
- Gunicorn/uWSGI

### Pasos de Despliegue
1. Configurar variables de entorno
2. Instalar dependencias: `pip install -r requirements.txt`
3. Ejecutar migraciones: `python manage.py migrate`
4. Recopilar estáticos: `python manage.py collectstatic`
5. Configurar servidor web
6. Iniciar aplicación con Gunicorn

### Docker (Opcional)
```bash
docker-compose up -d
```

---

## Mantenimiento

### Backups
- Accede a "Backups" desde el menú de administración
- Los backups incluyen la base de datos completa
- Descarga y guarda backups regularmente

### Actualizaciones
1. Hacer backup completo
2. Actualizar código
3. Ejecutar migraciones: `python manage.py migrate`
4. Recopilar estáticos: `python manage.py collectstatic`
5. Reiniciar servidor

---

## Troubleshooting

### Problemas Comunes

#### Error de migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

#### Archivos estáticos no se cargan
```bash
python manage.py collectstatic
```

#### Error de permisos
- Verificar que el usuario tenga permisos de escritura en `media/` y `logs/`

#### Base de datos bloqueada
- Cerrar todas las conexiones
- Reiniciar el servidor

---

## Contribución

### Estilo de Código
- Seguir PEP 8
- Docstrings en todas las funciones
- Comentarios en código complejo

### Commits
- Mensajes descriptivos
- Un cambio por commit cuando sea posible

---

## Licencia

Este proyecto es de uso privado. Todos los derechos reservados.

