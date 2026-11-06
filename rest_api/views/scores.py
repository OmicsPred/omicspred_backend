from .common import *

class RestListScores(generics.ListAPIView):
    """
    Retrieve the Genetic Scores
    Endpoint: /api/score/all
    """
    serializer_class = ScoreLightSerializer

    def get_queryset(self):
        request_obj = self.request
        include_ancestry = normalize_query_param(request_obj,'include_ancestry')
        # Fetch all the Scores
        if include_ancestry and str(include_ancestry) == '1':
            self.serializer_class = ScoreSerializer
        website = normalize_query_param(request_obj,'website')
        # Only website table
        if website and str(website) == '1':
            self.serializer_class = ScoreWebsiteLightSerializer
            queryset = Score.objects.only(*only_dict['score_website']).select_related(*related_dict['score_dataset_full']).all().order_by('num')
        else:
            queryset = get_score_queryset_base()
        queryset = queryset.prefetch_related(*related_dict['molecular_traits']).order_by('num')
        # Filter by list of Score IDs
        ids_list = get_ids_list(request_obj)
        if ids_list:
            queryset = queryset.filter(id__in=ids_list)

        # Table filter data - FOR PRIVATE USE CASE
        table_filter = normalize_query_param(request_obj,'table_filter')
        queryset = filter_data(queryset, table_filter)
        # Sort data
        queryset = sort_data_list(request_obj,'score',queryset)
        return queryset


class RestScore(generics.RetrieveAPIView):
    """
    Retrieve one Genetic Score
    Endpoint: /api/score/<opgs_id>
    """

    def get(self, request, opgs_id):
        opgs_id = opgs_id.upper()
        include_pathway = normalize_query_param(request,'include_pathway')
        queryset = get_score_queryset_base()
        try:
            if include_pathway and str(include_pathway)=='1':
                queryset = queryset.prefetch_related('genes__pathways','genes__pathways__superpathways','metabolites__pathways','metabolites__pathways__superpathways').get(id=opgs_id)
                # queryset = Score.objects.defer(*defer_dict['scores_defer']).select_related(*related_dict['score_dataset_full']).prefetch_related('genes__pathways','genes__pathways__superpathways','metabolites__pathways','metabolites__pathways__superpathways').get(id=opgs_id)
            else:
                queryset = queryset.get(id=opgs_id)
                # queryset = Score.objects.defer(*defer_dict['scores_defer']).select_related(*related_dict['score_dataset_full']).get(id=opgs_id)
        except Score.DoesNotExist:
            queryset = None
        if include_pathway and str(include_pathway)=='1':
            serializer = ScorePathwaySerializer(queryset,many=False)
        else:
            serializer = ScoreSerializer(queryset,many=False)

        return Response(serializer.data)


class RestScoreWithPerformance(generics.RetrieveAPIView):
    """
    Retrieve one Genetic Score (PGS) with performance data
    Endpoint: /api/score/performance/<opgs_id>
    """

    def get(self, request, opgs_id):
        opgs_id = opgs_id.upper()
        try:
            queryset = Score.objects.select_related(*related_dict['score_dataset_full']).prefetch_related('score_performance','score_performance__sample','score_performance__sample__cohorts','score_performance__performance_metric').get(id=opgs_id)
        except Score.DoesNotExist:
            queryset = None
        serializer = ScorePerformanceSerializer(queryset,many=False)
        return Response(serializer.data)


class RestScoreSearchByMolecularTrait(generics.ListAPIView):
    """
    Search the Genetic Score(s) using molecular trait name/id
    Endpoint: /api/score/search/<type>/<molecular_trait>
    """
    serializer_class = ScoreSerializer

    def get_queryset(self):
        molecular_trait_type = self.kwargs['type']
        molecular_trait = self.kwargs['molecular_trait']
        query_list = []
        queryset = []

        if molecular_trait_type and molecular_trait_type in ('gene','protein','metabolite') and molecular_trait:
            query_name_filter = {f'{molecular_trait_type}s__name__iexact': molecular_trait}
            query_id_filter = {f'{molecular_trait_type}s__external_id__iexact': molecular_trait}
            query_list = [Q(**query_name_filter), Q(**query_id_filter)]
        if query_list:
            include_performance_metrics = normalize_query_param(self.request,'include_performance_metrics')
            include_performance_data = normalize_query_param(self.request,'include_performance_data')
            # Add the performance metrics data structure
            if include_performance_metrics and str(include_performance_metrics) == '1':
                self.serializer_class = ScorePerformanceSerializer
                queryset = Score.objects.defer(*defer_dict['scores_defer']).select_related(*related_dict['score_dataset_full']).filter(reduce(operator.or_,query_list)).prefetch_related(*related_dict['molecular_traits'],'score_performance','score_performance__sample','score_performance__sample__cohorts','score_performance__performance_metric')
            # Add the performance metrics condensed data (for web display on tables) - PRIVATE parameter
            elif include_performance_data and str(include_performance_data) == '1':
                self.serializer_class = ScorePerformanceDataSerializer
                queryset = Score.objects.defer(*defer_dict['scores_defer']).select_related(*related_dict['score_dataset_full']).filter(reduce(operator.or_,query_list)).prefetch_related(*related_dict['molecular_traits'],*related_dict['performance_cohorts'])
            # Metadata without performance metrics information - PUBLIC parameter
            else:
                queryset = Score.objects.defer(*defer_dict['scores_defer']).select_related(*related_dict['score_dataset_full']).filter(reduce(operator.or_,query_list)).prefetch_related(*related_dict['molecular_traits'])

            # Filter data - FOR PRIVATE USE CASE
            filter_term = normalize_query_param(self.request,'filter')
            if filter_term and filter_term is not None:
                queryset = queryset.filter(Q(id__iexact=filter_term) |
                                           Q(dataset__id__iexact=filter_term) | Q(dataset__name__icontains=filter_term) |
                                           Q(dataset__platform__name__iexact=filter_term) | Q(dataset__platform__platform_master__type__iexact=filter_term) |
                                           Q(dataset__publication__id__iexact=filter_term) | Q(dataset__publication__firstauthor__iexact=filter_term))
        # Sort data + distinct scores
        queryset = sort_data_list(self.request,'score',queryset, distinct_col=['num'])
        # # Distinct scores
        # queryset = queryset.distinct('num')

        return queryset


class RestScoreSearch(generics.ListAPIView):
    """
    Search the Genetic Score(s) using parameters as query
    Endpoint: /api/score/search?<parameter(s)>
    """

    def get_queryset(self):
        request_obj = self.request
        include_ancestry = normalize_query_param(request_obj,'include_ancestry')
        # Fetch all the Scores
        if str(include_ancestry) == '0':
            self.serializer_class = ScoreLightSerializer
        else:
            self.serializer_class = ScoreSerializer
        queryset = Score.objects.defer(*defer_dict['scores_defer']).select_related(*related_dict['score_dataset_full']).all().prefetch_related(*related_dict['molecular_traits']).order_by('num')
        params = 0

        # Search by list of Score IDs
        opgs_ids = normalize_query_param(request_obj,'opgs_ids')
        if opgs_ids and opgs_ids is not None:
            opgs_ids = opgs_ids.upper()
            opgs_ids_list = opgs_ids.split(',')
            queryset = queryset.filter(id__in=opgs_ids_list)
            params += 1

        # Search by Publication (ID and PubMed ID)
        (params, queryset) = filter_by_publication(request_obj, queryset, params)
        (params, queryset) = filter_by_pmid(request_obj, queryset, params)

        # Search by Platform
        (params, queryset) = filter_by_platform(request_obj, queryset, params)

        # Search by Dataset
        (params, queryset) = filter_by_dataset(request_obj, queryset, params)

        # Search by Cohort
        cohort = normalize_query_param(request_obj,'cohort')
        cohort_training = normalize_query_param(request_obj,'cohort_training')
        cohort_validation = normalize_query_param(request_obj,'cohort_validation')
        if cohort and cohort is not None:
            queryset = queryset.filter(score_performance__sample__cohorts__name_short__iexact=cohort)
            # queryset = queryset.filter(score_performance__sample__cohorts__name_short__iexact=cohort).prefetch_related(*related_dict['score_search_cohort'])
            params += 1
        elif cohort_training and cohort_training is not None:
            queryset = queryset.filter(Q(score_performance__sample__cohorts__name_short__iexact=cohort_training),Q(score_performance__eval_type='T'))
            # queryset = queryset.filter(Q(score_performance__sample__cohorts__name_short__iexact=cohort_training),Q(score_performance__eval_type='T')).prefetch_related(*related_dict['score_search_cohort'])
            params += 1
        elif cohort_validation and cohort_validation is not None:
            queryset = queryset.filter(Q(score_performance__sample__cohorts__name_short__iexact=cohort_validation),~Q(score_performance__eval_type='T'))
            # queryset = queryset.filter(Q(score_performance__sample__cohorts__name_short__iexact=cohort_validation),~Q(score_performance__eval_type='T')).prefetch_related(*related_dict['score_search_cohort'])
            params += 1

        # Search by Tissue ID
        tissue_id = normalize_query_param(request_obj,'tissue_id')
        if tissue_id and tissue_id is not None:
            tissue_id = tissue_id.upper().replace(':','_')
            queryset = queryset.filter(dataset__tissue__id__iexact=tissue_id)
            params += 1

        # Filter data - FOR PRIVATE USE CASE
        filter_term = normalize_query_param(request_obj,'filter')
        if filter_term and filter_term is not None:
            query_filter_list = [Q(id__iexact=filter_term), Q(name__iexact=filter_term), Q(dataset__name__iexact=filter_term), Q(dataset__platform__platform_master__type__iexact=filter_term)]
            opd_id = normalize_query_param(request_obj,'opd_id')
            if (not opd_id or opd_id == None) and len(filter_term) == OPD_LENGTH and filter_term.upper().startswith(OPD_PREFIX):
                dataset_num = get_dataset_num(filter_term)
                query_filter_list.append(Q(dataset__num=dataset_num))
            opp_id = normalize_query_param(request_obj,'opp_id')
            if (not opp_id or opp_id == None) and len(filter_term) == opp_length and filter_term.upper().startswith(opp_prefix):
                publication_num = get_publication_num(filter_term)
                query_filter_list.append(Q(dataset__publication__num=publication_num))
            platform = normalize_query_param(request_obj,'platform')
            if not platform or platform == None:
                query_filter_list.append(Q(dataset__platform__name__iexact=filter_term))
            # Genes
            query_filter_list.extend([Q(genes__external_id__iexact=filter_term), Q(genes__name__icontains=filter_term)])
            # Proteins
            query_filter_list.extend([Q(proteins__external_id__iexact=filter_term), Q(proteins__name__icontains=filter_term)])
            # Metabolites
            query_filter_list.extend([Q(metabolites__external_id__iexact=filter_term), Q(metabolites__name__icontains=filter_term)])

            queryset = queryset.filter(reduce(operator.or_,query_filter_list))

        # Table filter data - FOR PRIVATE USE CASE
        table_filter = normalize_query_param(self.request,'table_filter')
        if table_filter and table_filter is not None:
            queryset = filter_data(queryset, table_filter)
            params += 1

        if params == 0:
            queryset = []
        else:
            # Sort data + distinct scores
            queryset = sort_data_list(self.request,'score',queryset,distinct_col=['num'])
            # # Distinct scores
            # queryset = queryset.distinct('num')

        return queryset
