# Guía de Deployment en Render

Esta guía te ayudará a desplegar tu aplicación Django en Render.

## Requisitos Previos

1. Una cuenta en [Render.com](https://render.com)
2. Tu proyecto en un repositorio Git (GitHub, GitLab, etc.)

## Pasos para el Deployment

### 1. Preparar el Repositorio

Asegúrate de que todos los cambios estén committeados y pusheados a tu repositorio:

```bash
git add .
git commit -m "Preparar proyecto para deployment en Render"
git push
```

### 2. Crear Base de Datos PostgreSQL en Render

1. Ve a tu dashboard en Render
2. Haz clic en "New +" y selecciona "PostgreSQL"
3. Configura:
   - **Name**: control-stock-db (o el nombre que prefieras)
   - **Database**: Deja el predeterminado
   - **User**: Deja el predeterminado
   - **Region**: Elige la región más cercana
   - **Plan**: Free (para empezar)
4. Haz clic en "Create Database"
5. **IMPORTANTE**: Guarda la "Internal Database URL" o "External Database URL" (la necesitarás después)

### 3. Crear Servicio Web en Render

1. En tu dashboard, haz clic en "New +" y selecciona "Web Service"
2. Conecta tu repositorio
3. Configura el servicio:
   - **Name**: control-stock (o el nombre que prefieras)
   - **Environment**: Python 3
   - **Region**: La misma que elegiste para la base de datos
   - **Branch**: main (o la rama que uses)
   - **Root Directory**: Deja vacío (si el proyecto está en la raíz)
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn control_stock.wsgi:application`

### 4. Configurar Variables de Entorno

En la sección "Environment Variables" del servicio web, agrega:

- **SECRET_KEY**: Genera una nueva clave secreta. Puedes usar:
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
  O usa el generador automático de Render si está disponible.

- **DEBUG**: `False`

- **ALLOWED_HOSTS**: Tu URL de Render (ejemplo: `control-stock-xxxx.onrender.com`) separado por comas si tienes múltiples dominios

- **DATABASE_URL**: La URL de tu base de datos PostgreSQL. Render debería proporcionar esto automáticamente si agregas la base de datos como dependencia, o puedes copiarla manualmente desde el panel de la base de datos.

### 5. Opcional: Configurar con render.yaml

Si prefieres usar el archivo `render.yaml` incluido en el proyecto:

1. Render detectará automáticamente el archivo `render.yaml` en la raíz del repositorio
2. Puedes hacer clic en "Apply" desde el dashboard de Render
3. Render creará tanto la base de datos como el servicio web automáticamente

**Nota**: Tendrás que ajustar el valor de `ALLOWED_HOSTS` en `render.yaml` con el nombre real de tu servicio.

### 6. Desplegar

1. Haz clic en "Create Web Service" (o "Apply" si usas render.yaml)
2. Render comenzará a construir y desplegar tu aplicación
3. Puedes ver el progreso en los logs

### 7. Ejecutar Migraciones y Crear Superusuario

Una vez que el servicio esté desplegado:

1. Abre la consola del servicio web en Render (shell)
2. Ejecuta las migraciones (si no se ejecutaron automáticamente):
   ```bash
   python manage.py migrate
   ```
3. Crea un superusuario:
   ```bash
   python manage.py createsuperuser
   ```

### 8. Configurar Comandos Iniciales (Opcional)

Si necesitas ejecutar comandos personalizados como crear categorías o importar productos:

1. Usa la consola shell de Render
2. O agrega estos comandos al `build.sh` si quieres que se ejecuten automáticamente durante el build

## Archivos Estáticos y Media

- Los archivos estáticos se servirán automáticamente mediante WhiteNoise
- Para los archivos media (imágenes de productos, facturas), considera usar un servicio de almacenamiento como:
  - AWS S3
  - Cloudinary
  - Render Disk (para desarrollo, no recomendado para producción)
  
**⚠️ ADVERTENCIA IMPORTANTE**: Render no persiste los archivos en el sistema de archivos entre deployments, por lo que cualquier archivo subido se perderá. Es crucial configurar un servicio de almacenamiento externo para producción si necesitas que los archivos media persistan.

### Configurar Almacenamiento en la Nube (Recomendado)

Para usar AWS S3 o Cloudinary, necesitarás:

1. Instalar el paquete correspondiente (django-storages para S3, django-cloudinary-storage para Cloudinary)
2. Actualizar `settings.py` para configurar `DEFAULT_FILE_STORAGE`
3. Agregar las credenciales como variables de entorno

Ejemplo con django-storages y S3:
```python
# En settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
```

## Tesseract OCR

Este proyecto utiliza Tesseract OCR para procesar facturas. Render no tiene Tesseract preinstalado, por lo que necesitarás una de las siguientes opciones:

### Opción 1: Instalar Tesseract en el build.sh (Recomendado)

Agrega estas líneas al inicio de `build.sh`:

```bash
# Instalar Tesseract OCR
apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-spa
```

**Nota**: Esto puede aumentar el tiempo de build y el tamaño de la imagen.

### Opción 2: Usar un servicio OCR externo

Considera migrar a un servicio OCR en la nube como:
- Google Cloud Vision API
- AWS Textract
- Azure Computer Vision

Esto es más escalable y no requiere instalación de dependencias del sistema.

## Solución de Problemas

### Error: "No module named 'xxx'"
- Verifica que todas las dependencias estén en `requirements.txt`

### Error: "DisallowedHost"
- Verifica que `ALLOWED_HOSTS` incluya tu dominio de Render

### Error de Base de Datos
- Verifica que `DATABASE_URL` esté configurada correctamente
- Asegúrate de que la base de datos esté activa en Render

### Archivos estáticos no se cargan
- Verifica que `collectstatic` se ejecute en el build
- Verifica que WhiteNoise esté en `INSTALLED_APPS` y `MIDDLEWARE`

### Problemas con Tesseract OCR
- Render no tiene Tesseract preinstalado. Necesitarás:
  1. Usar un buildpack personalizado, o
  2. Instalar Tesseract en el build.sh, o
  3. Considerar usar un servicio OCR externo como Google Cloud Vision API

## Recursos Adicionales

- [Documentación de Render para Django](https://render.com/docs/deploy-django)
- [Documentación de WhiteNoise](https://whitenoise.readthedocs.io/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)

