from .common import *

class RestListScorePheWAS(generics.ListAPIView):
    """
    Retrieve all the PheWAS entries
    Endpoint: /api/score/phewas/all
    """
    serializer_class = ScorePheWASSerializer

    def get_queryset(self):
        queryset = ScorePheWAS.objects.select_related(*related_dict['score_phewas_select']).all().prefetch_related(*related_dict['score_phewas']).order_by('score__id','trait_reported')

        # Table filter data - FOR PRIVATE USE CASE
        table_filter = normalize_query_param(self.request,'table_filter')
        queryset = filter_data(queryset, table_filter)

        # Filter data - FOR PRIVATE USE CASE
        filter_term = normalize_query_param(self.request,'filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(id__iexact=filter_term) |
                                       Q(phenotypes__id__iexact=filter_term) | Q(phenotypes__label__iexact=filter_term) |
                                       Q(publication__id__iexact=filter_term) | Q(publication__firstauthor__iexact=filter_term) |
                                       Q(phenotypes__id__iexact=filter_term) | Q(phenotypes__label__iexact=filter_term) |
                                       Q(method_description__icontains=filter_term) | Q(trait_reported__icontains=filter_term))

        # Sort data
        queryset = sort_data_list(self.request,'score_phewas',queryset,'score_id')

        return queryset


class RestScorePheWAS(generics.ListAPIView):
    """
    Retrieve all the PheWAS entries associated with a Genetic Score
    Endpoint: /api/score/phewas/<opgs_id>
    """
    serializer_class = ScorePheWASSerializer

    def get_queryset(self):
        opgs_id = self.kwargs['opgs_id']
        opgs_id = opgs_id.upper()

        queryset = ScorePheWAS.objects.select_related(*related_dict['score_phewas_select']).filter(score__id=opgs_id).prefetch_related(*related_dict['score_phewas']).order_by('pvalue')

        return queryset


class RestScorePheWASSearch(generics.ListAPIView):
    """
    Search the PheWAS entries using parameters as query
    Endpoint: /api/score/phewas/search?<parameter(s)>
    """
    serializer_class = ScorePheWASSerializer

    def get_queryset(self):

        queryset = ScorePheWAS.objects.select_related(*related_dict['score_phewas_select']).all().prefetch_related(*related_dict['score_phewas']).order_by('score_id')
        params = 0

        # Search by list of Score IDs
        opgs_ids = normalize_query_param(self.request,'opgs_ids')
        if opgs_ids and opgs_ids is not None:
            opgs_ids = opgs_ids.upper()
            opgs_ids_list = opgs_ids.split(',')
            queryset = queryset.filter(score__id__in=opgs_ids_list)
            params += 1

        # Search by Publication (ID and PubMed ID)
        opp_id = normalize_query_param(self.request,'opp_id')
        if opp_id and opp_id is not None:
            if opp_id.upper().startswith(OPP_PREFIX):
                publication_num = get_publication_num(opp_id)
                queryset = queryset.filter(Q(dataset__publication__num=publication_num))
            # queryset = queryset.filter(Q(dataset__publication__id__iexact=opp_id))
            params += 1
        pmid = normalize_query_param(self.request,'pmid')
        if pmid and pmid.isnumeric():
            queryset = queryset.filter(dataset__publication__pmid=pmid)
            params += 1

        # Search by Platform
        platform = normalize_query_param(self.request,'platform')
        if platform and platform is not None:
            queryset = queryset.filter(dataset__platform__name__iexact=platform)
            params += 1

        # Search by OmicsPred Dataset ID
        opd_id = normalize_query_param(self.request,'opd_id')
        if opd_id and opd_id is not None:
            dataset_num = get_dataset_num(opd_id)
            queryset = queryset.filter(dataset__num=dataset_num)
            # queryset = queryset.filter(dataset__id__iexact=opd_id)
            params += 1

        # Search by Phenotype ID (EFO)
        phenotype_id = normalize_query_param(self.request,'phenotype_id')
        if phenotype_id and phenotype_id is not None:
            queryset = queryset.filter(phenotypes__id=phenotype_id)
            params += 1

        # table_filter = normalize_query_param(request,'table_filter')
        # if table_filter and table_filter is not None:
        #     queryset = filter_data(queryset, table_filter)
        #     params += 1

        # Filter data - FOR PRIVATE USE CASE
        filter_term = normalize_query_param(self.request,'filter')
        if filter_term and filter_term is not None:
            query_filter_list = [ Q(score__genes__external_id__iexact=filter_term), Q(score__genes__name__icontains=filter_term),
                                  Q(score__proteins__external_id__iexact=filter_term), Q(score__proteins__name__iexact=filter_term),
                                  Q(score__metabolites__external_id__iexact=filter_term), Q(score__metabolites__name__icontains=filter_term),
                                  Q(samples__cohorts__name_short__iexact=filter_term), Q(samples__source_gwas_catalog__icontains=filter_term)]
            if not opgs_ids or opgs_ids == None:
                query_filter_list.extend([Q(score__id__iexact=filter_term), Q(score__name__icontains=filter_term)])
            if not opp_id or opp_id == None:
                query_filter_list.extend([Q(dataset__id__iexact=filter_term), Q(dataset__name__iexact=filter_term)])
            if not phenotype_id or phenotype_id == None:
                query_filter_list.extend([Q(phenotypes__id__iexact=filter_term), Q(phenotypes__label__icontains=filter_term)])
            if not platform or platform == None:
                query_filter_list.extend([Q(dataset__platform__name__iexact=filter_term), Q(dataset__platform__platform_master__type__iexact=filter_term)])
            queryset = queryset.filter(reduce(operator.or_,query_filter_list))

        if params == 0:
            queryset = []
        else:
            # Sort data + distinct score phewas
            queryset = sort_data_list(self.request,'score_phewas',queryset,'score_id',distinct_col=['score_id','pvalue','adjusted_pvalue'])

        return queryset