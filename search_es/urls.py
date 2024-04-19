from django.urls import re_path
from .views import *

slash = '/?'

rest_urls = {
    'es_search': 'es_search/search',
}

urlpatterns = [
    # ElasticSearch
    re_path (r'^'+rest_urls['es_search']+slash, ESSearch.as_view(), name="esSearch"),
]