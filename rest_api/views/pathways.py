from django.db.models.functions import Lower
from .common import *

class RestListPathways(generics.ListAPIView):
    """
    Retrieve all the Pathways
    Endpoint: /api/pathway/all
    """
    serializer_class = PathwaySerializerExtendedCount

    def get_queryset(self):
        # Fetch all the Pathways
        queryset = Pathway.objects.all().prefetch_related(*related_dict['pathway_prefetch_with_counts']).order_by(Lower('name'))

        # Filter data - FOR PRIVATE USE CASE
        filter_term = normalize_query_param(self.request,'filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(external_id__iexact=filter_term) | Q(name__icontains=filter_term) |
                                       Q(superpathways__external_id__iexact=filter_term) | Q(superpathways__name__icontains=filter_term))
        # Sort data
        queryset = sort_data_list(self.request,'pathway',queryset,'name')
        return queryset


class RestPathway(generics.RetrieveAPIView):
    """
    Retrieve one Pathway
    Endpoint: /api/pathway/<pathway_id>
    """

    def get(self, request, pathway_id):
        try:
            queryset = Pathway.objects.prefetch_related(*related_dict['pathway_prefetch_with_counts']).get(Q(name__iexact=pathway_id) | Q(external_id__iexact=pathway_id))
        except Pathway.DoesNotExist:
            queryset = None

        serializer = PathwaySerializerExtendedCount(queryset,many=False)
        return Response(serializer.data)


