from django import template
from pretix.multidomain.urlreverse import build_absolute_uri

register = template.Library()


@register.simple_tag()
def organizer_url(organizer, urlname):
    return build_absolute_uri(organizer, urlname)
