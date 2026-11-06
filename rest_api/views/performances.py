from .common import *

class RestPerformanceSearch(generics.ListAPIView):
    """
    Retrieve the Performance metric(s) using query
    Endpoint: /api/performance/search
    """
    serializer_class = PerformanceSerializer

    def get_queryset(self):
        request_obj = self.request
        queryset = Performance.objects.select_related(*related_dict['perf_select']).all().prefetch_related('sample__cohorts','performance_metric').order_by('id')
        params = 0

        # Search by Score ID
        (params, queryset) = filter_by_score(request_obj, queryset, params)

        # Search by Publication
        (params, queryset) = filter_by_publication(request_obj, queryset, params)
        (params, queryset) = filter_by_pmid(request_obj, queryset, params)

         # Search by Platform
        (params, queryset) = filter_by_platform(request_obj, queryset, params)

        # Search by Gene
        gene = normalize_query_param(self.request,'gene')
        if gene and gene is not None:
            queryset = queryset.filter(Q(score__genes__external_id__iexact=gene) | Q(score__genes__name__iexact=gene)).prefetch_related('score__genes')
            params += 1

        # Search by Protein
        protein = normalize_query_param(self.request,'protein')
        if protein and protein is not None:
            queryset = queryset.filter(Q(score__proteins__external_id__iexact=protein) | Q(score__proteins__name__iexact=protein)).prefetch_related('score__proteins')
            params += 1

        # Search by Metabolite
        metabolite = normalize_query_param(self.request,'metabolite')
        if metabolite and metabolite is not None:
            queryset = queryset.filter(Q(score__metabolites__external_id__iexact=metabolite) | Q(score__metabolites__name__iexact=metabolite)).prefetch_related('score__metabolites')
            params += 1
       
        if params == 0:
            queryset = []
        else:
            # Distinct performance
            queryset = queryset.distinct('id')

        return queryset


class RestPerformanceSearchByMolecularTrait(generics.ListAPIView):
    """
    Search the Performance metric(s) using molecular trait name/id
    Endpoint: /api/performance/search/<type>/<molecular_trait>
    """
    serializer_class = PerformanceSerializer

    def get_queryset(self):
        request_obj = self.request
        molecular_trait_type = self.kwargs['type']
        molecular_trait = self.kwargs['molecular_trait']
        query_list = []
        queryset = []

        if molecular_trait_type and molecular_trait_type in ('gene','protein','metabolite') and molecular_trait:
            query_name_filter = {f'score__{molecular_trait_type}s__name__iexact': molecular_trait}
            query_id_filter = {f'score__{molecular_trait_type}s__external_id__iexact': molecular_trait}
            query_list = [Q(**query_name_filter), Q(**query_id_filter)]

        if query_list:
            queryset = Performance.objects.select_related(*related_dict['perf_select']).filter(reduce(operator.or_,query_list)).prefetch_related('sample__cohorts','performance_metric',f'score__{molecular_trait_type}s').order_by('id')

            # Search by Score ID
            queryset = filter_by_score(request_obj, queryset)

            # Search by Publication
            queryset = filter_by_publication(request_obj, queryset)
            queryset = filter_by_pmid(request_obj, queryset)

            # Search by Platform
            queryset = filter_by_platform(request_obj, queryset)


        # Sort data
        queryset = sort_data_list(self.request,'performance',queryset,'score_id')
        # Distinct performance
        # queryset = queryset.distinct('id','score_id')

        return queryset