from .common import *

class RestListPhenotypes (generics.ListAPIView):
    """
    Retrieve all the Phenotypes
    Endpoint: /api/phenotype/all
    """
    serializer_class = PhenotypeSerializerScoresCount

    def get_queryset(self):
        request_obj = self.request
        queryset = Phenotype.objects.all()

        # Filter by list of EFO IDs
        ids_list = get_ids_list(request_obj)
        if ids_list:
            queryset = queryset.filter(id__in=ids_list)

        # Filter data - FOR PRIVATE USE CASE
        filter_term = normalize_query_param(request_obj,'filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(id__iexact=filter_term) | Q(label__icontains=filter_term) |
                                       Q(category__iexact=filter_term) | Q(label__icontains=filter_term))

        queryset = sort_data_list(request_obj,'phenotype',queryset,'label')

        return queryset


class RestPhenotype(generics.RetrieveAPIView):
    """
    Retrieve the Phenotype information
    Endpoint: /api/phenotype/<phenotype_id>
    """

    def get(self, request, phenotype_id):
        try:
            queryset = Phenotype.objects.get(id=phenotype_id)
        except Phenotype.DoesNotExist:
            queryset = None
        serializer = PhenotypeSerializerScoresCount(queryset,many=False)
        return Response(serializer.data)