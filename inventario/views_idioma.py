"""
Vistas para cambio de idioma
"""
from django.shortcuts import redirect
from django.utils import translation
from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.translation import get_language, activate


def cambiar_idioma(request):
    """
    Cambia el idioma del sistema.
    
    En Django 5.2+, el LocaleMiddleware busca el idioma en la sesión
    usando la clave 'django_language' (que es el valor por defecto de
    LANGUAGE_COOKIE_NAME).
    
    Acepta tanto POST (con CSRF) como GET (fallback).
    """
    # Obtener idioma de POST o GET
    if request.method == 'POST':
        idioma = request.POST.get('idioma', 'es')
    else:
        idioma = request.GET.get('idioma', 'es')
    
    # Validar que el idioma esté en la lista de idiomas permitidos
    idiomas_permitidos = [lang[0] for lang in settings.LANGUAGES]
    if idioma not in idiomas_permitidos:
        idioma = settings.LANGUAGE_CODE.split('-')[0]  # Usar solo el código base
    
    # Normalizar idioma (solo código base, sin variantes)
    idioma = idioma.split('-')[0].lower()
    
    # Activar el idioma para esta request
    activate(idioma)
    
    # Guardar el idioma en la sesión
    # El LocaleMiddleware busca esta clave específica
    request.session['django_language'] = idioma
    
    # También guardar en una clave personalizada para nuestro context processor
    request.session['language'] = idioma
    
    # Marcar la sesión como modificada para asegurar que se guarde
    request.session.modified = True
    
    # Forzar guardado de sesión explícitamente
    try:
        request.session.save()
    except Exception:
        pass  # Si falla, continuar de todas formas
    
    # Crear respuesta de redirección
    next_url = request.META.get('HTTP_REFERER', '/')
    # Si no hay referer, usar inicio
    if not next_url or next_url == request.build_absolute_uri():
        next_url = '/'
    
    response = HttpResponseRedirect(next_url)
    
    # Guardar también en cookie para persistencia entre sesiones
    # Django usa 'django_language' por defecto
    cookie_name = getattr(settings, 'LANGUAGE_COOKIE_NAME', 'django_language')
    cookie_age = getattr(settings, 'LANGUAGE_COOKIE_AGE', 60 * 60 * 24 * 365)  # 1 año por defecto
    cookie_path = getattr(settings, 'LANGUAGE_COOKIE_PATH', '/')
    cookie_domain = getattr(settings, 'LANGUAGE_COOKIE_DOMAIN', None)
    cookie_secure = getattr(settings, 'LANGUAGE_COOKIE_SECURE', False)
    cookie_httponly = getattr(settings, 'LANGUAGE_COOKIE_HTTPONLY', False)
    cookie_samesite = getattr(settings, 'LANGUAGE_COOKIE_SAMESITE', 'Lax')
    
    response.set_cookie(
        cookie_name,
        idioma,
        max_age=cookie_age,
        path=cookie_path,
        domain=cookie_domain,
        secure=cookie_secure,
        httponly=cookie_httponly,
        samesite=cookie_samesite,
    )
    
    return response

