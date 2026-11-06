from .common import *

class RestInfo(generics.RetrieveAPIView):
    """
    Return diverse information related to the REST API and the PGS Catalog
    Endpoint: /api/info
    """

    def get(self, request):
        data_count = {}
        for info in Info.objects.all().order_by('id'):
            data_count[info.name] = info.value
        data = {
            'rest_api': {
                "version": settings.REST_API_VERSION
            },
            'data_count': data_count
        }

        return Response(data)


class RestListExternalSources(generics.ListAPIView):
    """
    Retrieve all the External Sources
    Endpoint: /api/external_source/all
    """
    serializer_class = ExternalSourceSerializer

    def get_queryset(self):
        return ExternalSource.objects.all()
