"""
URL configuration for OmicsPred project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
# from django.urls import include, path, re_path
from django.urls import include, path

# Settings-specific configuration
from django.conf import settings


urlpatterns = [
    path('', include('rest_api.urls'))
]

# Allow to build search indexes by importing the module
if settings.IS_TEST == False:
    if settings.OP_ON_GAE == 0:
        from search_es import indexes
    urlpatterns.append(path('', include('search_es.urls')))

# Debug SQL queries
if settings.DEBUG:
    from django.urls import include
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    from django.conf.urls.static import static