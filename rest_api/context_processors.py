from django.conf import settings


def op_settings(request):
    return {
        'is_public_site' : settings.PUBLIC_SITE
    }