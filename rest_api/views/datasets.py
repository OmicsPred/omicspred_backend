from .common import *

class RestListDatasets(generics.ListAPIView):
    """
    Retrieve all the Datasets
    Endpoint: /api/dataset/all
    """
    serializer_class = DatasetSerializer

    def get_queryset(self):
        request_obj = self.request
        queryset = Dataset.objects.select_related(*related_dict['dataset_select']).all().prefetch_related(*related_dict['dataset_prefetch']).order_by('num')
        # Filter PheWAS study only - FOR PRIVATE USE CASE
        only_phewas = normalize_query_param(self.request,'only_phewas')
        if only_phewas and only_phewas is not None:
            queryset = queryset.filter(phewas_count__gt=0)
            self.serializer_class = DatasetPheWASPublicationSerializer

        # Add ancestry distribution for the website forms - FOR PRIVATE USE CASE
        website = normalize_query_param(request_obj,'website')
        if website and str(website) == '1':
            self.serializer_class = DatasetAncestrySerializer

        # queryset = filter_by_ancestry(request_obj, queryset, 'dataset')
        table_filter = normalize_query_param(request_obj,'table_filter')
        queryset = filter_data(queryset, table_filter,'dataset')

        return queryset


class RestDataset(generics.RetrieveAPIView):
    """
    Retrieve one Dataset
    Endpoint: /api/dataset/<opd_id>
    """

    def get(self, request, opd_id):
        opd_id = opd_id.upper()
        try:
            queryset = Dataset.objects.select_related(*related_dict['dataset_select']).prefetch_related(*related_dict['dataset_prefetch']).get(id=opd_id)
        except Dataset.DoesNotExist:
            queryset = None
        serializer = DatasetSerializer(queryset,many=False)
        return Response(serializer.data)


class RestDatasetSearch(generics.ListAPIView):
    """
    Retrieve the Dataset information from a given platform and/or PubMed ID
    Endpoint: /api/dataset/search
    """
    serializer_class = DatasetSerializer

    def get_queryset(self):
        request_obj = self.request
        try:
            # Database filtering
            queryset = Dataset.objects.select_related(*related_dict['dataset_select']).prefetch_related(*related_dict['dataset_prefetch']).all().order_by('num')
            # Filter by publication
            opp_id = normalize_query_param(request_obj,'opp_id')
            if opp_id and opp_id is not None:
                if opp_id.upper().startswith(OPP_PREFIX):
                    publication_num = get_publication_num(opp_id)
                    queryset = queryset.filter(Q(publication__num=publication_num))
                # queryset = queryset.filter(Q(publication__id__iexact=opp_id))
            pmid = normalize_query_param(request_obj,'pmid')
            if pmid and pmid.isnumeric():
                queryset = queryset.filter(publication__pmid=pmid)
            # Filter by platform
            platform = normalize_query_param(request_obj,'platform')
            if platform and platform is not None:
                queryset = queryset.filter(platform__name__iexact=platform)
            # Search by Tissue ID
            tissue_id = normalize_query_param(request_obj,'tissue_id')
            if tissue_id and tissue_id is not None:
                tissue_id = tissue_id.upper().replace(':','_')
                queryset = queryset.filter(tissue__id__iexact=tissue_id)
            # Add ancestry distribution for the website forms - FOR PRIVATE USE CASE
            website = normalize_query_param(request_obj,'website')
            if website and str(website) == '1':
                self.serializer_class = DatasetAncestrySerializer
        except Dataset.DoesNotExist:
            queryset = []
        return queryset


