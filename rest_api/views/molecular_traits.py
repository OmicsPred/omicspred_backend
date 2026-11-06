from django.core.exceptions import MultipleObjectsReturned
from .common import *

class RestMetabolite(generics.RetrieveAPIView):
    """
    Retrieve one Metabolite
    Endpoint: /api/metabolite/<metabolite_id>
    """

    def get(self, request, metabolite_id):
        try:
            queryset = Metabolite.objects.prefetch_related(*related_dict['pathways'],'pathway_group').get(Q(name__iexact=metabolite_id) | Q(external_id__iexact=metabolite_id))
        except Metabolite.DoesNotExist:
            queryset = None

        # Include scores count - FOR PRIVATE USE CASE
        include_scores_count = normalize_query_param(request,'include_scores_count')
        if include_scores_count and str(include_scores_count)=='1':
            serializer = MetaboliteSerializerExtendedScoresCount(queryset,many=False)
        else:
            serializer = MetaboliteSerializerExtended(queryset,many=False)
        return Response(serializer.data)


class RestProtein(generics.RetrieveAPIView):
    """
    Retrieve one Protein
    Endpoint: /api/protein/<protein_id>
    """

    def get(self, request, protein_id):
        try:
            queryset = Protein.objects.prefetch_related(*related_dict['pathways']).get(Q(name__iexact=protein_id) | Q(external_id__iexact=protein_id))
        except Protein.DoesNotExist:
            queryset = None
        except MultipleObjectsReturned:
            # Issue when more than 1 entry match the "protein_id" (usually the name).
            # Returns the entry without an external ID or the first entry if there are more than 1 match.
            try:
                queryset = Protein.objects.prefetch_related(*related_dict['pathways']).get(Q(name__iexact=protein_id) & Q(external_id__isnull=True))
            except MultipleObjectsReturned:
                queryset = Protein.objects.filter(Q(name__iexact=protein_id) & Q(external_id__isnull=True)).prefetch_related(*related_dict['pathways']).first()
            except Protein.DoesNotExist:
                queryset = None

        # Include scores count - FOR PRIVATE USE CASE
        include_scores_count = normalize_query_param(request,'include_scores_count')
        if include_scores_count and str(include_scores_count)=='1':
            serializer = ProteinSerializerExtendedScoresCount(queryset,many=False)
        else:
            serializer = ProteinSerializerExtended(queryset,many=False)
        return Response(serializer.data)


class RestGene(generics.RetrieveAPIView):
    """
    Retrieve one Gene, using its external ID
    Endpoint: /api/gene/<gene_id>
    """

    def get(self, request, gene_id):
        try:
            queryset = Gene.objects.prefetch_related(*related_dict['pathways']).get(external_id__iexact=gene_id)
        except Gene.DoesNotExist:
            queryset = None

        # Include scores count - FOR PRIVATE USE CASE
        include_scores_count = normalize_query_param(request,'include_scores_count')
        if include_scores_count and str(include_scores_count)=='1':
            serializer = GeneSerializerExtendedScoresCount(queryset,many=False)
        else:
            serializer = GeneSerializerExtended(queryset,many=False)
        return Response(serializer.data)


class RestSearchGene(generics.ListAPIView):
    """
    Search Genes
    Endpoint: /api/gene/search?
    """

    def get_queryset(self):
        request_obj = self.request
        queryset = Gene.objects.all().prefetch_related(*related_dict['pathways']).order_by('external_id')
        params = 0

        # Search by Gene name or external ID
        gene = normalize_query_param(self.request,'gene')
        if gene and gene is not None:
            queryset = queryset.filter(Q(name__iexact=gene) | Q(external_id__iexact=gene))
        params += 1

        # Search by Pathway
        (params, queryset) = filter_by_pathway(request_obj, queryset, params)

        # Filter data - FOR PRIVATE USE CASE
        filter_term = normalize_query_param(self.request,'filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(external_id__iexact=filter_term) | Q(name__icontains=filter_term) | Q(description__icontains=filter_term))

        # Include scores count - FOR PRIVATE USE CASE
        include_scores_count = normalize_query_param(self.request,'include_scores_count')
        if include_scores_count and str(include_scores_count)=='1':
            self.serializer_class = GeneSerializerExtendedScoresCount
            queryset = queryset.prefetch_related('gene_score')
        else:
            self.serializer_class = GeneSerializerExtended

        if params == 0:
            queryset = []

        return queryset


class RestSearchProtein(generics.ListAPIView):
    """
    Search Proteins
    Endpoint: /api/protein/search?
    """

    def get_queryset(self):
        request_obj = self.request
        queryset = Protein.objects.select_related('gene').all().prefetch_related(*related_dict['pathways']).order_by('external_id')
        params = 0

        # Search by Gene
        gene = normalize_query_param(self.request,'gene')
        if gene and gene is not None:
            queryset = queryset.filter(Q(gene__name__iexact=gene) | Q(gene__external_id__iexact=gene))
            params += 1

        # Search by Pathway
        (params, queryset) = filter_by_pathway(request_obj, queryset, params)

        # Filter data - FOR PRIVATE USE CASE
        filter_term = normalize_query_param(self.request,'filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(external_id__iexact=filter_term) | Q(name__icontains=filter_term) | Q(description__icontains=filter_term))

        # Include scores count - FOR PRIVATE USE CASE
        include_scores_count = normalize_query_param(self.request,'include_scores_count')
        if include_scores_count and str(include_scores_count)=='1':
            self.serializer_class = ProteinSerializerExtendedScoresCount
            queryset = queryset.prefetch_related('protein_score')
        else:
            self.serializer_class = ProteinSerializerExtended

        if params == 0:
            queryset = []

        return queryset


class RestSearchMetabolite(generics.ListAPIView):
    """
    Search Metabolites
    Endpoint: /api/metabolite/search?
    """

    def get_queryset(self):
        request_obj = self.request
        queryset = Metabolite.objects.all().prefetch_related(*related_dict['pathways']).order_by('external_id')
        params = 0

        # Search by Gene
        metabolite = normalize_query_param(request_obj,'metabolite')
        if metabolite and metabolite is not None:
            queryset = queryset.filter(Q(name__iexact=metabolite) | Q(external_id__iexact=metabolite))
            params += 1

        # Search by Pathway
        (params, queryset) = filter_by_pathway(request_obj, queryset, params)

        # Filter data - FOR PRIVATE USE CASE
        filter_term = normalize_query_param(request_obj,'filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(external_id__iexact=filter_term) | Q(name__icontains=filter_term))

        # Include scores count - FOR PRIVATE USE CASE
        include_scores_count = normalize_query_param(request_obj,'include_scores_count')
        if include_scores_count and str(include_scores_count)=='1':
            self.serializer_class = MetaboliteSerializerExtendedScoresCount
            queryset = queryset.prefetch_related('metabolite_score')
        else:
            self.serializer_class = MetaboliteSerializerExtended

        if params == 0:
            queryset = []

        return queryset
