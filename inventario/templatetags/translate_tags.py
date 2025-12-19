"""
Template tags para traducción simple
"""
from django import template
from inventario.translations import translate, get_translations_dict

register = template.Library()


@register.simple_tag
def trans(text):
    """
    Template tag para traducir texto
    
    Uso: {% trans "Texto a traducir" %}
    """
    return translate(text)


@register.simple_tag
def get_translations():
    """
    Template tag para obtener todas las traducciones como diccionario
    
    Uso: {% get_translations as translations %}
    """
    return get_translations_dict()

