from .common import *

class RestPlotSearch(generics.ListAPIView):
    """
    Search plot data
    Endpoint: /api/plot/search
    """

    serializer_class = PlotSerializer

    def get_queryset(self):
        request_obj = self.request
        queryset = Plot.objects.using('plot').all()
        params = 0

        # Search by Publication ID
        opp_id = normalize_query_param(request_obj,'opp_id')
        if opp_id and opp_id is not None:
            opp_id = opp_id.upper()
            if opp_id.startswith(OPP_PREFIX):
                queryset = queryset.filter(publication_id=opp_id)
            params += 1

        # Search by Pubmed ID
        pmid = normalize_query_param(request_obj,'pmid')
        if pmid and pmid.isnumeric():
            queryset = queryset.filter(pmid=pmid)
            params += 1

        # Search by platform
        platform = normalize_query_param(self.request,'platform')
        if platform and platform is not None:
            queryset = queryset.filter(platform_name__iexact=platform)
            params += 1

        # Search by dataset
        dataset = self.request.query_params.get('dataset')
        if dataset and dataset is not None:
            dataset = dataset.upper()
            if dataset.startswith(OPD_PREFIX):
                queryset = queryset.filter(dataset_id=dataset)
                params += 1

        if params == 0:
            queryset = []

        return queryset


class RestPlotFileSearch(generics.RetrieveAPIView):
    """
    Retrieve performance metrics for a given platform.
    Used to generate the plot data file
    Endpoint: /api/plot/file/search
    """

    serializer_class = ScorePlotSerializer

    def get(self, request):
        request_obj = self.request
        queryset = Performance.objects.only('score_id','dataset__id','dataset__platform__id','dataset__platform__name','dataset__publication__pmid','eval_type','cohort_label').select_related('dataset','dataset__publication','dataset__platform').all().prefetch_related('performance_metric').order_by('score_id')
        params = 0

        # Search by platform
        (params, queryset) = filter_by_platform(request_obj, queryset, params)

        # Search by Publication
        (params, queryset) = filter_by_publication(request_obj, queryset, params)
        (params, queryset) = filter_by_pmid(request_obj, queryset, params)

        # Search by Dataset
        (params, queryset) = filter_by_dataset(request_obj, queryset, params)

        if params == 0:
            queryset = []

        data = []
        cohort_cols = {}
        cohort_cols_names = []

        score_ids_list = [x.score_id for x in queryset]
        score_ids = set(score_ids_list)
        # print(score_ids)
        score_idx = {}
        new_score_ids = list(score_ids)
        for idx, score_id in enumerate(new_score_ids):
            score_idx[score_id] = idx
        # print(score_idx)
        # for score in queryset:
        for perf in queryset:
            perf_score_id = perf.score_id
            idx = perf_score_id
            cohort_name = perf.cohort_label
            if perf.eval_type == 'T':
                cohort_name += ' (internal validation)'
            # found_missing_rate = False
            for metric in perf.performance_metrics:
                metric_name = metric['name_short']
                metric_type = metric_name.replace(' ','')
                # if metric_type == 'MissingRate':
                #     found_missing_rate = True
                if 'estimate' in metric.keys():
                    estimate = metric['estimate']
                else:
                    estimate = None

                colname = f'{cohort_name}_{metric_type}'
                # Cohort estimate
                if colname not in cohort_cols_names:
                    cohort_cols[colname] = { "name": cohort_name, "title": colname, "type": f'_{metric_type}' ,  "data": {} }
                    cohort_cols_names.append(colname)
                cohort_cols[colname]["data"][idx] = estimate
            for col in cohort_cols.keys():
                if idx not in cohort_cols[col]["data"].keys():
                    cohort_cols[col]["data"][idx] = None
                # if idx != 0:
                #     if missing_index not in cohort_cols[col]["data"].keys():
                #         cohort_cols[col]["data"][missing_index] = None

        # Final check to avoid missing entries
        for score_id in score_idx.keys():
            for col in cohort_cols.keys():
                if score_id not in cohort_cols[col]["data"].keys():
                    cohort_cols[col]["data"][score_id] = None

        # for colname in sorted(cohort_cols_names):
        for colname in cohort_cols_names:
            cohort_data = {}
            for key in cohort_cols[colname].keys():
                # Sort data
                if key == 'data':
                    # sorted_data = dict(sorted(cohort_cols[colname][key].items()))
                    # new_sorted_data = [{str(key): val for key, val in sorted_data.items()}]
                    cohort_data[key] = dict(sorted(cohort_cols[colname][key].items()))
                else:
                   cohort_data[key] = cohort_cols[colname][key]

            # data.append(cohort_cols[colname])
            data.append(cohort_data)

        return Response(data)


class RestPlotScoreSearch(generics.ListAPIView):
    """
    Retrieve the score information for the searched platform, in order to add information to the data plot (for the same platform in RestPlotSearch)
    Used to generate the plot data file
    Endpoint: /api/plot/score/search
    """
    serializer_class = ScorePlotSerializer

    def get_queryset(self):
        request_obj = self.request
        params = 0
        queryset = Score.objects.select_related(*related_dict['score_dataset_full']).all().prefetch_related('genes','transcripts','proteins','metabolites').order_by('num')

        # Search by platform
        (params, queryset) = filter_by_platform(request_obj, queryset, params) 

        # Search by Publication
        (params, queryset) = filter_by_publication(request_obj, queryset, params)
        (params, queryset) = filter_by_pmid(request_obj, queryset, params)
        
        # Search by Dataset
        (params, queryset) = filter_by_dataset(request_obj,queryset, params)

        if params == 0:
            queryset = []
            
        return queryset

