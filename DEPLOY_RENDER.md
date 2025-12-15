# 🚀 Guía de Despliegue en Render

Esta guía te ayudará a desplegar tu proyecto Django en Render de forma rápida y sencilla.

## 📋 Requisitos Previos

1. Cuenta en [Render.com](https://render.com) (gratis)
2. Tu proyecto en GitHub, GitLab o Bitbucket
3. 10 minutos de tu tiempo

## 🎯 Pasos para Desplegar

### 1. Subir tu código a GitHub

Si aún no tienes tu código en GitHub:

```bash
# Inicializar repositorio (si no lo has hecho)
git init
git add .
git commit -m "Preparado para producción"

# Crear repositorio en GitHub y luego:
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git branch -M main
git push -u origin main
```

### 2. Crear cuenta en Render

1. Ve a [render.com](https://render.com)
2. Regístrate con tu cuenta de GitHub (más fácil)
3. Confirma tu email

### 3. Crear nuevo Web Service

1. En el dashboard de Render, haz clic en **"New +"** → **"Web Service"**
2. Conecta tu repositorio de GitHub
3. Selecciona el repositorio `proyecto_boti`

### 4. Configurar el Servicio

Render detectará automáticamente el archivo `render.yaml`, pero puedes configurar manualmente:

**Configuración Básica:**
- **Name:** `control-stock` (o el nombre que prefieras)
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- **Start Command:** `gunicorn control_stock.wsgi:application`

**Variables de Entorno:**
Haz clic en "Environment" y agrega:

```
SECRET_KEY=tu-secret-key-super-segura-aqui
DEBUG=False
ALLOWED_HOSTS=tu-app.onrender.com
```

**Para generar un SECRET_KEY seguro:**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Configurar Base de Datos (Opcional pero Recomendado)

Para producción, es mejor usar PostgreSQL en lugar de SQLite:

1. En Render, crea un **PostgreSQL Database** (gratis)
2. Copia la **Internal Database URL**
3. En las variables de entorno de tu Web Service, agrega:
   ```
   DATABASE_URL=postgresql://usuario:password@host:5432/dbname
   ```

Luego actualiza `settings.py` para usar PostgreSQL (ver sección siguiente).

### 6. Esperar el Despliegue

Render construirá y desplegará tu aplicación automáticamente. Esto puede tomar 5-10 minutos la primera vez.

### 7. Ejecutar Migraciones y Crear Superusuario

Una vez desplegado, necesitas:

1. Abre la consola web de Render (en el dashboard de tu servicio, pestaña "Shell")
2. Ejecuta:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py crear_categorias
```

### 8. ¡Listo! 🎉

Tu aplicación estará disponible en: `https://tu-app.onrender.com`

## 🔧 Configuración Avanzada

### Usar PostgreSQL en lugar de SQLite

Si creaste una base de datos PostgreSQL, actualiza `settings.py`:

```python
import dj_database_url

# Al final del archivo settings.py, reemplaza DATABASES con:
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3'),
        conn_max_age=600
    )
}
```

Y agrega `dj-database-url` a `requirements.txt`:
```
dj-database-url>=2.1.0
```

### Configurar Dominio Personalizado

1. En el dashboard de tu servicio, ve a "Settings"
2. En "Custom Domain", agrega tu dominio
3. Sigue las instrucciones para configurar DNS

## ⚠️ Notas Importantes

- **Tesseract OCR**: Render instalará Tesseract automáticamente gracias al `build.sh`
- **Archivos Media**: Los archivos subidos se guardan en el sistema de archivos de Render. Para producción real, considera usar S3 o similar.
- **Plan Gratuito**: Render tiene un plan gratuito, pero el servicio se "duerme" después de 15 minutos de inactividad. La primera petición puede tardar ~30 segundos en despertar.

## 🐛 Solución de Problemas

### Error: "No module named 'gunicorn'"
- Verifica que `gunicorn` esté en `requirements.txt`

### Error: "Static files not found"
- Asegúrate de que `collectstatic` se ejecute en el build command
- Verifica que `whitenoise` esté en `requirements.txt` y en `MIDDLEWARE`

### Error: "Tesseract not found"
- Verifica que `build.sh` tenga permisos de ejecución
- Revisa los logs de build en Render

### La app se "duerme"
- Esto es normal en el plan gratuito
- Considera el plan Starter ($7/mes) para evitar esto

## 📞 Soporte

Si tienes problemas, revisa los logs en Render Dashboard → Tu Servicio → Logs

¡Buena suerte con tu despliegue! 🚀

