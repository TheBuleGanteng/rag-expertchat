import os
from django import template

register = template.Library()

@register.filter(name='filename_filter')
def filename_filter(value):
    """Extract the filename from the file path."""
    return os.path.basename(value)