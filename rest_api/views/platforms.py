from .common import *

class RestListPlatforms(generics.ListAPIView):
    """
    Retrieve all the Platforms
    Endpoint: /api/platform/all
    """
    serializer_class = PlatformMasterSerializer
    queryset = PlatformMaster.objects.all().prefetch_related(*related_dict['platform_prefetch']).order_by('name')


class RestPlatform(generics.RetrieveAPIView):
    """
    Retrieve one Platform
    Endpoint: /api/platform/<platform>
    """

    def get(self, request, platform):
        try:
            queryset = PlatformMaster.objects.prefetch_related(*related_dict['platform_prefetch']).get(name__iexact=platform)
        except PlatformMaster.DoesNotExist:
            queryset = None
        serializer = PlatformMasterSerializer(queryset,many=False)
        return Response(serializer.data)