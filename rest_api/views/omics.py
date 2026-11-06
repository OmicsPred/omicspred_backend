from .common import *

class RestMetabolomics(generics.ListAPIView):
    """
    Fetch Scores from metabolomic platform
    Endpoint: /api/metabolomics/<platform>
    """
    serializer_class = ScorePerformanceMetaboliteSerializer

    def get_queryset(self):
        request_obj = self.request
        # Platform
        platform = self.kwargs['platform']

        performance_metrics = normalize_query_param(request_obj,'include_performance_metrics')
        if str(performance_metrics) == '0':
            queryset = Score.objects.only(*only_dict['scores_pp_table']).select_related(*related_dict['score_dataset']).all().prefetch_related(*related_dict['metabolites']).order_by('num')
            self.serializer_class = ScoreMetaboliteSerializer
        else:
            queryset = Score.objects.only(*only_dict['scores_pp_table']).select_related(*related_dict['score_dataset']).all().prefetch_related(*related_dict['metabolites'],*related_dict['performance_cohorts']).order_by('num')

        ## Filters ##
        # Filter Dataset - FOR PRIVATE USE CASE
        ds_filter_found = 0
        (ds_filter_found, queryset) = filter_by_dataset(request_obj, queryset, ds_filter_found)

        # Add other filters if no dataset ID provided
        if ds_filter_found != 1:
            # Filter by platform name
            queryset = queryset.filter(dataset__platform__name__iexact=platform)

            # Filter Publication
            queryset = filter_by_publication(request_obj, queryset)
            queryset = filter_by_pmid(request_obj, queryset)

            # Filter Version
            queryset = filter_by_platform_version(request_obj, queryset)

        # Filter data - FOR PRIVATE USE CASE
        filter_term = normalize_query_param(request_obj,'filter')
        if filter_term and filter_term is not None:
            query_filter_list = [Q(id__iexact=filter_term), Q(name__iexact=filter_term), Q(trait_reported_id__iexact=filter_term), Q(trait_reported__icontains=filter_term)]
            dataset = normalize_query_param(request_obj,'dataset')
            if not dataset or dataset == None:
                query_filter_list.extend([Q(dataset__id__iexact=filter_term), Q(dataset__name__iexact=filter_term)])
            opp_id = normalize_query_param(request_obj,'opp_id')
            if (not opp_id or opp_id == None) and len(filter_term) == OPP_LENGTH and filter_term.upper().startswith(OPP_PREFIX):
                publication_num = get_publication_num(filter_term)
                query_filter_list.append(Q(dataset__publication__num=publication_num))
            # Metabolite old pathways
            query_filter_list.extend([Q(metabolites__pathway_group__name__iexact=filter_term), Q(metabolites__pathway_subgroup__name__iexact=filter_term)])
            # Metabolite
            query_filter_list.extend([Q(metabolites__external_id__iexact=filter_term), Q(metabolites__name__icontains=filter_term)])

            queryset = queryset.filter(reduce(operator.or_,query_filter_list))

        # Table filter data - FOR PRIVATE USE CASE
        table_filter = normalize_query_param(request_obj,'table_filter')
        queryset = filter_data(queryset, table_filter)

        # Sort data + distinct scores
        queryset = sort_data_list(request_obj,'score',queryset,distinct_col=['num'])
        # # Distinct scores
        # queryset = queryset.distinct('num')

        return queryset


class RestProteomics(generics.ListAPIView):
    """
    Fetch Scores from proteomic platform
    Endpoint: /api/proteomics/<platform>
    """
    serializer_class = ScorePerformanceProteinSerializer

    def get_queryset(self):
        request_obj = self.request
        # Platform
        platform = self.kwargs['platform']

        performance_metrics = normalize_query_param(request_obj,'include_performance_metrics')
        if str(performance_metrics) == '0':
            queryset = Score.objects.only(*only_dict['scores_pp_table']).select_related(*related_dict['score_dataset']).all().prefetch_related(*related_dict['proteins'],*related_dict['genes'])
            self.serializer_class = ScoreProteinSerializer
        else:
            queryset = Score.objects.only(*only_dict['scores_pp_table']).select_related(*related_dict['score_dataset']).all().prefetch_related(*related_dict['proteins'],*related_dict['genes'],*related_dict['performance_cohorts'])

        ## Filters ##
        # Filter Dataset - FOR PRIVATE USE CASE
        ds_filter_found = 0
        (ds_filter_found, queryset) = filter_by_dataset(request_obj, queryset, ds_filter_found)

        # Add other filters if no dataset ID provided
        if ds_filter_found != 1:
            # Filter by platform name
            queryset = queryset.filter(dataset__platform__name__iexact=platform)

            # Filter Publication
            queryset = filter_by_publication(request_obj, queryset)
            queryset = filter_by_pmid(request_obj, queryset)

            # Filter Version
            queryset = filter_by_platform_version(request_obj, queryset)

        # Filter platform versions - FOR PRIVATE USE CASE
        platform_versions = normalize_query_param(request_obj,'versions')
        if platform_versions and platform_versions is not None:
            platform_versions_list = platform_versions.split(';')
            queryset = queryset.filter(dataset__platform__version__in=platform_versions_list)

        # Filter data - FOR PRIVATE USE CASE
        filter_term = normalize_query_param(request_obj,'filter')
        if filter_term and filter_term is not None:
            query_filter_list = [Q(id__iexact=filter_term), Q(name__iexact=filter_term)]
            dataset = normalize_query_param(request_obj,'dataset')
            if not dataset or dataset == None:
                query_filter_list.extend([Q(dataset__id__iexact=filter_term), Q(dataset__name__iexact=filter_term)])
            version = normalize_query_param(request_obj,'version')
            if version and version is not None:
                query_filter_list.append(Q(dataset__platform__version__icontains=filter_term))
            opp_id = normalize_query_param(request_obj,'opp_id')
            if (not opp_id or opp_id == None) and len(filter_term) == OPP_LENGTH and filter_term.upper().startswith(OPP_PREFIX):
                publication_num = get_publication_num(filter_term)
                query_filter_list.append(Q(dataset__publication__num=publication_num))
                # query_filter_list.append(Q(dataset__publication__id__iexact=filter_term))
            # Proteins
            query_filter_list.extend([Q(proteins__external_id__iexact=filter_term), Q(proteins__name__icontains=filter_term)])
            # Genes
            query_filter_list.extend([Q(genes__external_id__iexact=filter_term), Q(genes__name__iexact=filter_term)])
            queryset = queryset.filter(reduce(operator.or_,query_filter_list))

        # Table filter data - FOR PRIVATE USE CASE
        table_filter = normalize_query_param(self.request,'table_filter')
        queryset = filter_data(queryset, table_filter)

        # Sort data + distinct scores
        # queryset = sort_data_list(self.request,'score',queryset)
        queryset = sort_data_list(self.request,'score',queryset,distinct_col=['num'])
        # # Distinct scores
        # queryset = queryset.distinct('num')

        return queryset


class RestTranscriptomics(generics.ListAPIView):
    """
    Fetch Scores from transcriptomic platform
    Endpoint: /api/transcriptomics/<platform>
    """
    serializer_class = ScorePerformanceTranscriptSerializer

    def get_queryset(self):
        request_obj = self.request
        # Platform
        platform = self.kwargs['platform']

        performance_metrics = normalize_query_param(request_obj,'include_performance_metrics')
        if str(performance_metrics) == '0':
            queryset = Score.objects.only(*only_dict['scores_pp_table']).select_related(*related_dict['score_dataset']).all().prefetch_related(*related_dict['genes'])
            self.serializer_class = ScoreTranscriptSerializer
        else:
            queryset = Score.objects.only(*only_dict['scores_pp_table']).select_related(*related_dict['score_dataset']).all().prefetch_related(*related_dict['genes'],*related_dict['performance_cohorts'])

        ## Filters ##
        # Filter Dataset - FOR PRIVATE USE CASE
        ds_filter_found = 0
        (ds_filter_found, queryset) = filter_by_dataset(request_obj, queryset, ds_filter_found)

        # Add other filters if no dataset ID provided
        if ds_filter_found != 1:
            # Filter by platform name
            queryset = queryset.filter(dataset__platform__name__iexact=platform)

            # Filter Publication
            queryset = filter_by_publication(request_obj, queryset)
            queryset = filter_by_pmid(request_obj, queryset)

            # Filter Version
            queryset = filter_by_platform_version(request_obj, queryset)

        # Filter data - FOR PRIVATE USE CASE
        filter_term = normalize_query_param(request_obj,'filter')
        if filter_term and filter_term is not None:
            query_filter_list = [Q(id__iexact=filter_term), Q(name__iexact=filter_term)]
            dataset = normalize_query_param(request_obj,'dataset')
            if not dataset or dataset == None:
                query_filter_list.extend([Q(dataset__id__iexact=filter_term), Q(dataset__name__icontains=filter_term)])
            opp_id = normalize_query_param(request_obj,'opp_id')
            if (not opp_id or opp_id == None) and len(filter_term) == OPP_LENGTH and filter_term.upper().startswith(OPP_PREFIX):
                publication_num = get_publication_num(filter_term)
                query_filter_list.append(Q(dataset__publication__num=publication_num))
                # query_filter_list.append(Q(dataset__publication__id__iexact=filter_term))
            # Genes
            query_filter_list.extend([Q(genes__external_id__iexact=filter_term), Q(genes__name__iexact=filter_term)])
            queryset = queryset.filter(reduce(operator.or_,query_filter_list))

        # Table filter data - FOR PRIVATE USE CASE
        # table_filter = normalize_query_param(request,'table_filter')
        # queryset = filter_data(queryset, table_filter)

        # Sort data + distinct scores
        # queryset = sort_data_list(self.request,'score',queryset,distinct_col=['num'])
        queryset = sort_data_list(request_obj,'score',queryset)
        # # Distinct scores
        # queryset = queryset.distinct('num')

        return queryset
