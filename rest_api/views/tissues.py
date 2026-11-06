from .common import *

class RestListTissues(generics.ListAPIView):
    """
    Retrieve all the Tissues
    Endpoint: /api/tissue/all
    """
    serializer_class = TissueSerializerScoresCount
    queryset = Tissue.objects.prefetch_related(*related_dict['tissue_prefetch']).all().order_by('label')


class RestTissue(generics.ListAPIView):
    """
    Retrieve the Tissue information from a given tissue (external ID or name)
    Endpoint: /api/tissue/<tissue>
    """
    def get(self, request, tissue):
        try:
            queryset = Tissue.objects.get(Q(label__iexact=tissue) | Q(id__iexact=tissue))
        except Tissue.DoesNotExist:
            queryset = None
        serializer = TissueSerializerScoresCount(queryset,many=False)
        return Response(serializer.data)