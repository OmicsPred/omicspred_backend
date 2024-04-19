import re
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from rest_framework.serializers import ValidationError
from django.db.models import Prefetch, Q, FloatField, DecimalField
from django.db.models.functions import Cast
from omicspred.models import *
from applications.models import *
from .serializers import *
# from search_es.search import get_search


generic_defer = ['curation_notes']
only_dict = {
    'scores_table': ['id','platform_id','variants_number','platform__id','platform__name'],
    'metabolite': ['id','name','external_id','pathway_group_id','pathway_subgroup_id','pathway_group__id','pathway_group__name','pathway_subgroup__id','pathway_subgroup__name']
}

performance_metric = [Prefetch('performance_metric', queryset=Metric.objects.only('id','performance_id','name_short','estimate').all())]
related_dict = {
    'metabolites': [Prefetch('metabolites', queryset=Metabolite.objects.only(*only_dict['metabolite']).select_related('pathway_group','pathway_subgroup').all().order_by('id'))],
    'proteins': [Prefetch('proteins', queryset=Protein.objects.only('id','name','external_id').all().order_by('id'))],
    'genes': [Prefetch('genes', queryset=Gene.objects.only('id','name','external_id').all().order_by('id'))],
    'genes_sources': [Prefetch('genes', queryset=Gene.objects.only('id','name','external_id','external_id_source').all().order_by('id'))],
    'performances': [Prefetch('score_performance', queryset=Performance.objects.defer('publication','efo').select_related('sample').all().prefetch_related('sample__cohorts','performance_metric').order_by('id'))],
    'performance_cohorts': [Prefetch('score_performance', queryset=Performance.objects.only('id','score_id','cohort_label').all().prefetch_related(*performance_metric).order_by('id'))],
    'perf_select': ['score', 'publication', 'platform', 'sample', 'efo'],
    'platform_add_select': ['platform','platform__platform_master','publication','tissue'],
    'platform_add_prefetch': ['samples_training','samples_training__cohorts','samples_validation','samples_validation__cohorts','platform__platform_score'],
    'platform_prefetch': ['platform_version','platform_version__platform_pp'],
    'publication_defer': [*generic_defer,'curation_status'],
    'publication_platforms': [Prefetch('platforms',queryset=PlatformAdditional.objects.select_related('platform','platform__platform_master','tissue').all().prefetch_related('samples_training','samples_training__cohorts','samples_validation','samples_validation__cohorts'))],
    'score_prefetch' : ['genes','transcripts','proteins','metabolites'],
    'score_applications_select': ['phecode','platform','platform__platform_master','cohort'],
    'search_by_select': ['publication','platform','platform__platform_master']
}
missing_index = 0


def sort_data_list(request,type,queryset,default_col='num'):
    # Sort data
    sort_field = request.query_params.get('sort_field')
    if sort_field:
        if sort_field == f'{type}_id':
            sort_field = 'id'
        elif sort_field == f'{type}_name':
            sort_field = 'name'
        elif sort_field.endswith(f'_name') and not sort_field.endswith(f'__name'):
            sort_field = sort_field.replace('_name','__name')
    sort = request.query_params.get('sort')
    if sort_field and sort_field is not None and sort and sort is not None:
        if sort == 'desc':
            sort_field = '-'+sort_field
        queryset = queryset.order_by(sort_field)
    else:
        queryset = queryset.order_by(default_col)
    print(f"SORTING: {sort_field} | {sort}")
    return queryset


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Over the fixed rate limit
    if isinstance(exc, Throttled): # check that a Throttled exception is raised
        response.data = { # custom response data
            'message': 'request limit exceeded',
            'availableIn': '%d seconds'%exc.wait
        }
    # Over the maximum number of results per page (limit parameter)
    elif isinstance(exc, ValidationError):
        formatted_exc = ''
        for type in exc.detail.keys():
            if formatted_exc != '':
                formatted_exc += '; '
            formatted_exc += exc.detail[type]
        response.data = { # custom response data
            'status_code': response.status_code,
            'message': formatted_exc
        }
    elif response.status_code == status.HTTP_404_NOT_FOUND:
        response.data = { # custom response data
            'status_code': status.HTTP_404_NOT_FOUND,
            'message': 'This REST endpoint does not exist'
        }
    elif response is not None:
        response.data = { # custom response data
            'status_code': response.status_code,
            'message': str(exc)
        }
    else:
        response.data = {
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'message': 'Internal Server Error'
        }
    return response


def get_ids_list(object):
    ids_list = []

    # List of IDs provided in the URL
    ids = object.request.query_params.get('filter_ids')
    if ids and ids is not None:
        ids = ids.upper()
        ids_list = ids.split(',')
    # List of IDs provided in a JSON object
    elif 'filter_ids' in object.request.data:
        ids_list = [ x.upper() for x in object.request.data['filter_ids']]
    return ids_list


## Cohorts ##

class RestListCohorts(generics.ListAPIView):
    """
    Retrieve all the Cohorts
    """
    serializer_class = CohortSerializer

    def get_queryset(self):
        queryset = Cohort.objects.all().order_by('name_short')
        # 'filter_ids' parameter: fetch the cohorts from the list of cohort short names
        names_list = get_ids_list(self)
        # Filter the query depending on the parameters used
        if names_list:
            names_list = r'^('+'|'.join(names_list)+')$'
            queryset = queryset.filter(name_short__iregex=names_list)

        return queryset


## Pathways ##

class RestListPathways(generics.ListAPIView):
    """
    Retrieve all the Pathways
    """
    # queryset = PathwayNew.objects.all().prefetch_related('superpathways','pathway_genes','pathway_metabolites')#.order_by('name')
    # queryset = PathwayNew.objects.all().prefetch_related('superpathways','pathway_genes','pathway_metabolites','pathway_metabolites__pathway_group','pathway_metabolites__pathway_subgroup').order_by('id')
    serializer_class = PathwaySerializerNewExtended

    def get_queryset(self):
        # Fetch all the Pathways
        queryset = PathwayNew.objects.all().prefetch_related('superpathways','pathway_genes','pathway_metabolites').order_by('name')

        # Filter data
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(external_id__iexact=filter_term) | Q(name__iexact=filter_term) |
                                       Q(pathway_genes__external_id__iexact=filter_term) | Q(pathway_genes__name__iexact=filter_term) |
                                       Q(pathway_metabolites__external_id__iexact=filter_term) | Q(pathway_metabolites__name__icontains=filter_term) |
                                       Q(superpathways__id__iexact=filter_term) | Q(superpathways__name__iexact=filter_term)).distinct()
        # Sort data
        queryset = sort_data_list(self.request,'pathway',queryset,'name')
        return queryset


class RestPathway(generics.RetrieveAPIView):
    """
    Retrieve one Pathway
    """

    def get(self, request, pathway_id):
        try:
            queryset = PathwayNew.objects.prefetch_related('superpathways','pathway_genes','pathway_metabolites').get(Q(name__iexact=pathway_id) | Q(external_id__iexact=pathway_id))
        except Gene.DoesNotExist:
            queryset = None
        serializer = PathwaySerializerNewExtended(queryset,many=False)
        return Response(serializer.data)


## Biological features ##
class RestMetabolite(generics.RetrieveAPIView):
    """
    Retrieve one Metabolite
    """

    def get(self, request, metabolite_id):
        try:
            queryset = Metabolite.objects.prefetch_related('pathway_group','pathways').get(Q(name__iexact=metabolite_id) | Q(external_id__iexact=metabolite_id))
        except Metabolite.DoesNotExist:
            queryset = None
        serializer = MetaboliteSerializerExtended(queryset,many=False)
        return Response(serializer.data)


class RestProtein(generics.RetrieveAPIView):
    """
    Retrieve one Protein
    """

    def get(self, request, protein_id):
        param_inc_gene = self.request.query_params.get('include_gene')
        try:
            queryset = Protein.objects.get(Q(name__iexact=protein_id) | Q(external_id__iexact=protein_id))
        except Protein.DoesNotExist:
            queryset = None
        if (param_inc_gene and str(param_inc_gene)=='1'):
            serializer = ProteinSerializerExtended(queryset,many=False)
        else:
            serializer = ProteinSerializer(queryset,many=False)
        return Response(serializer.data)


class RestGene(generics.RetrieveAPIView):
    """
    Retrieve one Gene
    """

    def get(self, request, gene_id):
        try:
            queryset = Gene.objects.prefetch_related('pathways').get(Q(name__iexact=gene_id) | Q(external_id__iexact=gene_id))
        except Gene.DoesNotExist:
            queryset = None
        serializer = GeneSerializerExtended(queryset,many=False)
        return Response(serializer.data)


class RestSearchProtein(generics.ListAPIView):
    """
    Search Proteins
    """
    serializer_class = ProteinSerializer

    def get_queryset(self):
        queryset = Protein.objects.select_related('gene').all().order_by('id')
        params = 0

        # Search by Gene
        gene_id = self.request.query_params.get('gene_id')
        if gene_id and gene_id is not None:
            queryset = queryset.filter(Q(gene__name__iexact=gene_id) | Q(gene__external_id__iexact=gene_id))
            params += 1

        if params == 0:
            queryset = []

        return queryset


## Omics by platform ##

class RestMetabolomics(generics.ListAPIView):
    serializer_class = ScoreMetaboliteSerializer

    def get_queryset(self):
        # Platform
        platform = self.kwargs['platform']
        queryset = Score.objects.only(*only_dict['scores_table']).select_related('platform').filter(platform__name__iexact=platform).prefetch_related(*related_dict['metabolites'],*related_dict['performance_cohorts']).distinct().order_by('num')

        # Filter data
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(id__iexact=filter_term) | Q(metabolites__external_id__iexact=filter_term) | Q(metabolites__name__icontains=filter_term))
        # Sort data
        queryset = sort_data_list(self.request,'score',queryset)
        # sort_field = self.request.query_params.get('sort_field')
        # sort = self.request.query_params.get('sort')
        # if sort_field and sort_field is not None and sort and sort is not None:
        #     if sort == 'desc':
        #         sort_field = '-'+sort_field
        #     queryset = queryset.order_by(sort_field)
        # else:
        #     queryset = queryset.order_by('num')
        return queryset


class RestProteomics(generics.ListAPIView):
    serializer_class = ScoreProteinSerializer

    def get_queryset(self):
        # Platform
        platform = self.kwargs['platform']
        queryset = Score.objects.only(*only_dict['scores_table']).select_related('platform').filter(platform__name__iexact=platform).prefetch_related(*related_dict['proteins'],*related_dict['genes'],*related_dict['performance_cohorts']).distinct()

        # Filter data
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(id__iexact=filter_term) | Q(proteins__external_id__iexact=filter_term) | Q(proteins__name__icontains=filter_term) | Q(genes__external_id__iexact=filter_term) | Q(genes__name__iexact=filter_term))
        # Filter platforms
        platform_versions = self.request.query_params.get('versions')
        if platform_versions and platform_versions is not None:
            platform_versions_list = platform_versions.split(';')
            queryset = queryset.filter(platform__version__in=platform_versions_list)
        # Sort data
        queryset = sort_data_list(self.request,'score',queryset)
        # sort_field = self.request.query_params.get('sort_field')
        # sort = self.request.query_params.get('sort')
        # if sort_field and sort_field is not None and sort and sort is not None:
        #     if sort == 'desc':
        #         sort_field = '-'+sort_field
        #     queryset = queryset.order_by(sort_field)
        # else:
        #     queryset = queryset.order_by('num')

        return queryset


class RestTranscriptomics(generics.ListAPIView):
    serializer_class = ScoreTranscriptSerializer

    def get_queryset(self):
        # Platform
        platform = self.kwargs['platform']
        queryset = Score.objects.only(*only_dict['scores_table']).select_related('platform').filter(platform__name__iexact=platform).prefetch_related(*related_dict['genes'],*related_dict['performance_cohorts']).distinct().order_by('num')

        # Filter data
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(id__iexact=filter_term) | Q(genes__external_id__iexact=filter_term) | Q(genes__name__iexact=filter_term))
        # Sort data
        queryset = sort_data_list(self.request,'score',queryset)
        return queryset


## Performance metrics ##

class RestListPerformances(generics.ListAPIView):
    """
    Retrieve all the Performance Metrics
    """
    queryset = Performance.objects.select_related(*related_dict['perf_select']).all().prefetch_related('sample__cohorts','performance_metric').order_by('id')
    serializer_class = PerformanceSerializer


class RestPerformanceSearch(generics.ListAPIView):
    """
    Retrieve the Performance metric(s) using query
    """
    serializer_class = PerformanceSerializer

    def get_queryset(self):

        queryset = Performance.objects.select_related(*related_dict['perf_select']).all().prefetch_related('sample__cohorts','performance_metric').order_by('id')
        params = 0

        # Search by Score ID
        opgs_id = self.request.query_params.get('opgs_id')
        if opgs_id and opgs_id is not None:
            opgs_id = opgs_id.upper()
            queryset = queryset.filter(score__id=opgs_id)
            params += 1

        # Search by PubMed ID
        pmid = self.request.query_params.get('pmid')
        if pmid and pmid.isnumeric():
            queryset = queryset.filter(publication__pmid=pmid)
            params += 1

        # Search by Platform
        platform = self.request.query_params.get('platform')
        if platform and platform is not None:
            queryset = queryset.filter(platform__name=platform)
            params += 1

        if params == 0:
            queryset = []

        return queryset


## Platforms ##

class RestListPlatforms(generics.ListAPIView):
    """
    Retrieve all the Platforms
    """
    serializer_class = PlatformMasterSerializer
    queryset = PlatformMaster.objects.all().prefetch_related(*related_dict['platform_prefetch']).order_by('name')


class RestPlatform(generics.RetrieveAPIView):
    """
    Retrieve one Platform
    """

    def get(self, request, platform):
        try:
            queryset = PlatformMaster.objects.prefetch_related(*related_dict['platform_prefetch']).get(name__iexact=platform)
        except Platform.DoesNotExist:
            queryset = None
        serializer = PlatformMasterSerializer(queryset,many=False)
        return Response(serializer.data)


class RestListPlatformAdditionals(generics.ListAPIView):
    """
    Retrieve all the PlatformAdditional
    """
    serializer_class = PlatformAdditionalSerializer
    queryset = PlatformAdditional.objects.select_related(*related_dict['platform_add_select']).all().prefetch_related(*related_dict['platform_add_prefetch'])


class RestPlatformAdditional(generics.ListAPIView):
    """
    Retrieve the Platform Additional information from a given platform
    """
    serializer_class = PlatformAdditionalSerializer

    def get_queryset(self):
        try:
            platform = self.kwargs['platform']
            # Database filtering
            queryset = PlatformAdditional.objects.select_related(*related_dict['platform_add_select']).prefetch_related(*related_dict['platform_add_prefetch']).filter(platform__name__iexact=platform)
        except PlatformAdditional.DoesNotExist:
            queryset = []
        return queryset


## Publications ##

class RestListPublications(generics.ListAPIView):
    """
    Retrieve the PGS Publications
    """
    serializer_class = PublicationExtendedSerializer

    def get_queryset(self):
        # Fetch all the Publications
        queryset = Publication.objects.defer(*related_dict['publication_defer']).all().prefetch_related(*related_dict['publication_platforms']).order_by('id')
        # Filter by list of Publications IDs
        pmids_list = get_ids_list(self)
        if pmids_list:
            queryset = queryset.filter(pmid__in=pmids_list)

        return queryset


class RestPublication(generics.RetrieveAPIView):
    """
    Retrieve one Publication
    """

    def get(self, request, pmid):
        try:
            # queryset = Publication.objects.get(pmid__iexact=pmid)
            queryset = Publication.objects.defer(*related_dict['publication_defer']).prefetch_related(*related_dict['publication_platforms']).get(pmid__iexact=pmid)
            # queryset = Publication.objects.defer(*related_dict['publication_defer']).prefetch_related('platforms','platforms__platform__platform_master','platforms__tissue','platforms__samples_training','platforms__samples_training__cohorts','platforms__samples_validation','platforms__samples_validation__cohorts').get(pmid__iexact=pmid)
        except Publication.DoesNotExist:
            queryset = None
        serializer = PublicationExtendedSerializer(queryset,many=False)
        return Response(serializer.data)


class RestPublicationSearch(generics.ListAPIView):
    """
    Retrieve the Publication(s) using query
    """
    serializer_class = PublicationExtendedSerializer

    def get_queryset(self):
        # queryset = Publication.objects.defer(*related_dict['publication_defer']).all().order_by('id')
        queryset = Publication.objects.defer(*related_dict['publication_defer']).all().prefetch_related(*related_dict['publication_platforms']).order_by('id')

        params = 0

        # Search by Score ID
        pgs_id = self.request.query_params.get('opgs_id')
        if pgs_id and pgs_id is not None:
            pgs_id = pgs_id.upper()
            try:
                score = Score.objects.only('id','publication__id').select_related('publication').get(id=pgs_id)
                queryset = queryset.filter(id=score.publication.id)
                params += 1
            except Score.DoesNotExist:
                queryset = []

        # Search by Author
        author = self.request.query_params.get('author')
        if author and author is not None:
            queryset = queryset.filter(authors__icontains=author)
            params += 1

        # Search by Pubmed ID
        pmid = self.request.query_params.get('pmid')
        if pmid and pmid.isnumeric():
            queryset = queryset.filter(pmid=pmid)
            params += 1

        if params == 0:
            queryset = []
        return queryset


## Samples ##

class RestListSamples(generics.ListAPIView):
    """
    Retrieve all the Samples
    """
    serializer_class = SampleSerializer
    queryset = Sample.objects.all().prefetch_related('cohorts').order_by('id')


## Scores ##

class RestListScores(generics.ListAPIView):
    """
    Retrieve the Polygenic Scores
    """
    serializer_class = ScoreSerializer

    def get_queryset(self):
        # Fetch all the Scores
        queryset = Score.objects.select_related('publication','platform','platform__platform_master').all().prefetch_related(*related_dict['score_prefetch']).order_by('num')

        # Filter by list of Score IDs
        ids_list = get_ids_list(self)
        if ids_list:
            queryset = queryset.filter(id__in=ids_list)

        # Filter data
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(id__iexact=filter_term) | Q(name__iexact=filter_term) |
                                       Q(genes__external_id__iexact=filter_term) | Q(genes__name__iexact=filter_term) |
                                       Q(proteins__external_id__iexact=filter_term) | Q(proteins__name__icontains=filter_term) |
                                       Q(metabolites__external_id__iexact=filter_term) | Q(metabolites__name__icontains=filter_term) |
                                       Q(platform__name__iexact=filter_term) | Q(publication__firstauthor__iexact=filter_term))
         # Sort data
        queryset = sort_data_list(self.request,'score',queryset)
        return queryset


class RestScore(generics.RetrieveAPIView):
    """
    Retrieve one Polygenic Score (PGS)
    """

    def get(self, request, opgs_id):
        opgs_id = opgs_id.upper()
        include_pathway = self.request.query_params.get('include_pathway')
        try:
            if include_pathway and include_pathway is not None:
                queryset = Score.objects.select_related('publication','platform').prefetch_related('genes__pathways','genes__pathways__superpathways','metabolites__pathways','metabolites__pathways__superpathways').get(id=opgs_id)
            else:
                queryset = Score.objects.select_related('publication','platform').get(id=opgs_id)
        except Score.DoesNotExist:
            queryset = None
        if include_pathway and include_pathway is not None:
            serializer = ScorePathwaySerializer(queryset,many=False)
        else:
            serializer = ScoreSerializer(queryset,many=False)

        return Response(serializer.data)


class RestScoreWithPerformance(generics.RetrieveAPIView):
    """
    Retrieve one Polygenic Score (PGS) with performance data
    """

    def get(self, request, opgs_id):
        opgs_id = opgs_id.upper()
        try:
            queryset = Score.objects.select_related('publication','platform').prefetch_related('score_performance','score_performance__sample','score_performance__sample__cohorts','score_performance__performance_metric').get(id=opgs_id)
        except Score.DoesNotExist:
            queryset = None
        serializer = ScorePerformanceSerializer(queryset,many=False)
        return Response(serializer.data)


class RestScoreSearchByGene(generics.ListAPIView):
    """
    Search the Polygenic Score(s) using gene name/id
    """
    serializer_class = ScoreSerializer

    def get_queryset(self):
        try:
            gene = self.kwargs['gene']
            # Database filtering
            queryset = Score.objects.select_related('publication','platform').filter(Q(genes__name__iexact=gene) | Q(genes__external_id__iexact=gene)).prefetch_related('genes','transcripts','proteins','metabolites').order_by('num')
        except Score.DoesNotExist:
            queryset = []
        return queryset


class RestScoreSearchByProtein(generics.ListAPIView):
    """
    Search the Polygenic Score(s) using protein name/id
    """
    serializer_class = ScoreSerializer

    def get_queryset(self):
        try:
            protein = self.kwargs['protein']
            # Database filtering
            queryset = Score.objects.select_related(*related_dict['search_by_select']).filter(Q(proteins__name__iexact=protein) | Q(proteins__external_id__iexact=protein)).prefetch_related('genes','transcripts','proteins','metabolites').order_by('num')
        except Score.DoesNotExist:
            queryset = []
        return queryset


class RestScoreSearchByProteinWithPerformance(generics.ListAPIView):
    """
    Search the Polygenic Score(s) using protein name/id
    """
    serializer_class = ScorePerformanceSerializer

    def get_queryset(self):
        try:
            protein = self.kwargs['protein']
            # Database filtering
            # queryset = Score.objects.select_related('publication','platform').filter(Q(proteins__name__iexact=protein) | Q(proteins__external_id__iexact=protein)).prefetch_related('genes','transcripts','proteins','metabolites').order_by('num')

            queryset = Score.objects.defer('transcripts','metabolites').select_related(*related_dict['search_by_select']).filter(Q(proteins__name__iexact=protein) | Q(proteins__external_id__iexact=protein)).prefetch_related('genes','proteins','score_performance','score_performance__sample','score_performance__sample__cohorts','score_performance__performance_metric').order_by('num')
        except Score.DoesNotExist:
            queryset = []
        return queryset


class RestScoreSearchByMetabolite(generics.ListAPIView):
    """
    Search the Polygenic Score(s) using metabolite name/id
    """
    serializer_class = ScoreSerializer

    def get_queryset(self):
        try:
            metabolite = self.kwargs['metabolite']
            # Database filtering
            queryset = Score.objects.select_related(*related_dict['search_by_select']).filter(Q(metabolites__name__iexact=metabolite) | Q(metabolites__external_id__iexact=metabolite)).prefetch_related('genes','transcripts','proteins','metabolites','metabolites__pathway_group','metabolites__pathway_subgroup').order_by('num')
        except Score.DoesNotExist:
            queryset = []
        return queryset


class RestScoreSearch(generics.ListAPIView):
    """
    Search the Polygenic Score(s) using query
    """
    serializer_class = ScoreSerializer

    def get_queryset(self):
        queryset = Score.objects.select_related('publication','platform').all().order_by('num')
        params = 0

        # Search by list of Score IDs
        opgs_ids = self.request.query_params.get('opgs_ids')
        if opgs_ids and opgs_ids is not None:
            opgs_ids = opgs_ids.upper()
            opgs_ids_list = opgs_ids.split(',')
            queryset = queryset.filter(id__in=opgs_ids_list)
            params += 1

        # Search by Pubmed ID
        pmid = self.request.query_params.get('pmid')
        if pmid and pmid.isnumeric():
            queryset = queryset.filter(publication__pmid=pmid)
            params += 1

        # Search by platform
        platform = self.request.query_params.get('platform')
        if platform and platform is not None:
            queryset = queryset.filter(platform__name__iexact=platform)
            params += 1

        # Filter data
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(id__iexact=filter_term) | Q(metabolites__external_id__iexact=filter_term) | Q(metabolites__name__icontains=filter_term))

        if params == 0:
            queryset = []

        return queryset


## Tables - format by column ##

class RestTableSearch(generics.ListAPIView):
    serializer_class = ScoreExtendedSerializer

    def get_queryset(self):
        queryset = Score.objects.select_related('publication','platform').all().order_by('num')
        params = 0

        # Search by platform
        platform = self.request.query_params.get('platform')
        if platform and platform is not None:
            queryset = queryset.filter(platform__name__iexact=platform)
            params += 1

        if params == 0:
            queryset = []

        return queryset


class RestMetaboliteTableSearch(generics.RetrieveAPIView):

    def get(self,request):
        #queryset = Score.objects.select_related('platform').all().prefetch_related('metabolites').order_by('num')
        queryset = Score.objects.only(*only_dict['scores_table']).select_related('platform').all().prefetch_related(*related_dict['performances'],*related_dict['metabolites']).order_by('num')

        # Search by platform
        platform = self.request.query_params.get('platform')
        if platform and platform is not None:
            queryset = queryset.filter(platform__name__iexact=platform)
        else:
            queryset = []

        data = []
        score_col = { "name": "OMICSPRED ID", "data": {} }

        if platform == 'Metabolon':
            metabolon_col = { "name": "Metabolon ID", "data": {} }
        else:
            metabolon_col = None

        metabo_col = { "name": "Biochemical Name", "data": {} }
        pathway_grp_col = { "name": "Pathway Group", "data": {} }
        pathway_subgrp_col = { "name": "Pathway Subgroup", "data": {} }
        variants_nb_col = { "name": "#SNP", "data": {} }
        cohort_cols = {}
        cohort_cols_names = []

        idx = 0
        for score in queryset:
            # OMICPRED ID
            score_col["data"][idx] = score.id

            # Metabolite Information
            metabolite = score.metabolites.all()[0]
            # - Metabolon ID
            if metabolon_col:
                metabolon_col["data"][idx] = metabolite.external_id
            # - Biochemical Name
            metabo_col["data"][idx] = metabolite.name
            # - Pathway Group
            pathway_group = None
            if metabolite.pathway_group:
                pathway_group = metabolite.pathway_group.name
            pathway_grp_col["data"][idx] = pathway_group
            # - Pathway Subgroup
            pathway_subgroup = None
            if metabolite.pathway_subgroup:
                pathway_subgroup = metabolite.pathway_subgroup.name
            pathway_subgrp_col["data"][idx] = pathway_subgroup

            # #SNP
            variants_nb_col["data"][idx] = score.variants_number

            for perf in score.score_performance.all():
                cohort_name = perf.sample.cohorts.all()[0].name_short
                for metric in perf.performance_metrics:
                    metric_name = metric['name_short']
                    if 'estimate' in metric.keys():
                        estimate = metric['estimate']
                    else:
                        estimate = ''

                    colname = f'{cohort_name}_{metric_name}'
                    collabel = f'{cohort_name} {metric_name}'
                    # Cohort estimate
                    if colname not in cohort_cols_names:
                        cohort_cols[colname] = { "name": collabel, "data": {} }
                        cohort_cols_names.append(colname)
                    cohort_cols[colname]["data"][idx] = estimate
                    # Cohort pvalue
                    # if 'pvalue' in metric.keys():
                    #     pvalue = metric['pvalue']
                    # else:
                    #     pvalue = ''
                    # pval_colname = f'{colname}_pvalue'
                    # pval_collabel = f'{colname} (p-value)'
                    # if pval_colname not in cohort_cols_names:
                    #     cohort_cols[pval_colname] = { "name": pval_collabel, "data": {} }
                    #     cohort_cols_names.append(pval_colname)
                    # cohort_cols[pval_colname]["data"][idx] = pvalue
            for col in cohort_cols.keys():
                if idx not in cohort_cols[col]["data"].keys():
                    cohort_cols[col]["data"][idx] = ''
                if idx != 0:
                    if missing_index not in cohort_cols[col]["data"].keys():
                        cohort_cols[col]["data"][missing_index] = ''
            idx += 1

        data.append(score_col)
        if metabolon_col:
            data.append(metabolon_col)
        data.append(metabo_col)
        data.append(pathway_grp_col)
        data.append(pathway_subgrp_col)
        data.append(variants_nb_col)

        for colname in cohort_cols_names:
            data.append(cohort_cols[colname])

        return Response(data)


class RestProteinTableSearch(generics.RetrieveAPIView):
    def get(self,request):
        queryset = Score.objects.only(*only_dict['scores_table']).select_related('platform').all().prefetch_related(*related_dict['performances'],*related_dict['genes'],*related_dict['proteins']).order_by('num')

        # Search by platform
        platform = self.request.query_params.get('platform')
        if platform and platform is not None:
            queryset = queryset.filter(platform__name__iexact=platform)
        else:
            queryset = []

        data = []
        score_col = { "name": "OMICSPRED ID", "data": {} }

        if platform == 'Somalogic':
            somascan_col = { "name": "SOMAscan ID", "data": {} }
        else:
            somascan_col = None

        uniprot_col = { "name": "UniProt ID", "data": {} }
        gene_col = { "name": "Gene", "data": {} }
        protein_col = { "name": "Protein", "data": {} }
        variants_nb_col = { "name": "#SNP", "data": {} }
        cohort_cols = {}
        cohort_cols_names = []

        idx = 0
        for score in queryset:
            # idx = f'"{idx}"'
            # OMICPRED ID
            score_col["data"][idx] = score.id
            # SOMAscan ID
            if somascan_col:
                somascan_col["data"][idx] = score.name

            # Protein Information
            # Sorting later instead of using the queryset method "order_by" to avoid generating more SQL queries
            proteins = [x for x in score.proteins.all()]
            # - UniProt ID(s)
            uniprot_ids = set()
            for protein_id in sorted([x.external_id for x in proteins]):
                if protein_id:
                    uniprot_ids.add(protein_id)
            uniprot_col["data"][idx] = ';'.join(uniprot_ids)
            # - Protein name(s)
            protein_names = set()
            for protein_name in sorted([x.name for x in proteins]):
                if protein_name:
                    protein_names.add(protein_name)
            protein_col["data"][idx] = ';'.join(protein_names)

            # Gene informatiom
            gene_names = set()
            # Sorting later instead of using the queryset method "order_by" to avoid generating more SQL queries
            for gene_name in sorted([x.name for x in score.genes.all()]):
                if gene_name:
                    gene_names.add(gene_name)
            gene_col["data"][idx] = ';'.join(gene_names)

            # #SNP
            variants_nb_col["data"][idx] = score.variants_number

            for perf in score.score_performance.all():
                cohort_name = perf.sample.cohorts.all()[0].name_short
                for metric in perf.performance_metrics:
                    metric_name = metric['name_short']
                    if 'estimate' in metric.keys():
                        estimate = metric['estimate']
                    else:
                        estimate = ''

                    colname = f'{cohort_name}_{metric_name}'
                    collabel = f'{cohort_name} {metric_name}'
                    # Cohort estimate
                    if colname not in cohort_cols_names:
                        cohort_cols[colname] = { "name": collabel, "data": {} }
                        cohort_cols_names.append(colname)
                    cohort_cols[colname]["data"][idx] = estimate
            #         # Cohort pvalue
            #         # if 'pvalue' in metric.keys():
            #         #     pvalue = metric['pvalue']
            #         # else:
            #         #     pvalue = ''
            #         # pval_colname = f'{colname}_pvalue'
            #         # pval_collabel = f'{colname} (p-value)'
            #         # if pval_colname not in cohort_cols_names:
            #         #     cohort_cols[pval_colname] = { "name": pval_collabel, "data": {} }
            #         #     cohort_cols_names.append(pval_colname)
            #         # cohort_cols[pval_colname]["data"][idx] = pvalue
            for col in cohort_cols.keys():
                if idx not in cohort_cols[col]["data"].keys():
                    cohort_cols[col]["data"][idx] = ''
                if idx != 0:
                    if missing_index not in cohort_cols[col]["data"].keys():
                        cohort_cols[col]["data"][missing_index] = ''
            idx += 1

        data.append(score_col)
        if somascan_col:
            data.append(somascan_col)
        data.append(uniprot_col)
        data.append(gene_col)
        data.append(protein_col)
        data.append(variants_nb_col)

        for colname in cohort_cols_names:
            data.append(cohort_cols[colname])

        return Response(data)


class RestTranscriptTableSearch(generics.RetrieveAPIView):

    def get(self,request):
        # queryset = Score.objects.select_related('platform').all().prefetch_related('genes').order_by('num')
        queryset = Score.objects.only(*only_dict['scores_table']).select_related('platform').all().prefetch_related(*related_dict['performances'],*related_dict['genes_sources']).order_by('num') # transcripts

        # Search by platform
        platform = self.request.query_params.get('platform')
        if platform and platform is not None:
            queryset = queryset.filter(platform__name__iexact=platform)
        else:
            queryset = []

        data = []
        score_col = { "name": "OMICSPRED ID", "data": {} }

        ensembl_col = { "name": "Ensembl ID", "data": {} }
        gene_col = { "name": "Gene", "data": {} }
        # transcript_col = { "name": "Transcript", "data": {} }
        variants_nb_col = { "name": "#SNP", "data": {} }
        cohort_cols = {}
        cohort_cols_names = []

        idx = 0
        for score in queryset:
            # idx = f"{idx}"
            # OMICPRED ID
            score_col["data"][idx] = score.id

            # Gene informatiom
            ensembl_ids = set()
            gene_names = set()
            # Sorting later instead of using the queryset method "order_by" to avoid generating more SQL queries
            genes = score.genes.all()
            for gene in sorted(genes, key=lambda x: x.name):
                if gene.external_id and gene.external_id_source == 'Ensembl':
                        ensembl_ids.add(gene.external_id)
                if gene.name:
                    gene_names.add(gene.name)
            ensembl_col["data"][idx] = ';'.join(ensembl_ids)
            gene_col["data"][idx] = ';'.join(gene_names)

            # # Transcript informatiom
            # transcript_names = set()
            # for transcript in score.transcripts.all().order_by('name'):
            #     if transcript.name:
            #         transcript_names.add(transcript.name)
            # transcript_col["data"][idx] = ';'.join(transcript_names)
            # #SNP
            variants_nb_col["data"][idx] = score.variants_number

            for perf in score.score_performance.all():
                cohort_name = perf.sample.cohorts.all()[0].name_short
                for metric in perf.performance_metrics:
                    metric_name = metric['name_short']
                    if 'estimate' in metric.keys():
                        estimate = metric['estimate']
                    else:
                        estimate = ''

                    colname = f'{cohort_name}_{metric_name}'
                    collabel = f'{cohort_name} {metric_name}'
                    # Cohort estimate
                    if colname not in cohort_cols_names:
                        cohort_cols[colname] = { "name": collabel, "data": {} }
                        cohort_cols_names.append(colname)
                    cohort_cols[colname]["data"][idx] = estimate

                    # Cohort pvalue
                    # if 'pvalue' in metric.keys():
                    #     pvalue = metric['pvalue']
                    # else:
                    #     pvalue = ''
                    # pval_colname = f'{colname}_pvalue'
                    # pval_collabel = f'{colname} (p-value)'
                    # if pval_colname not in cohort_cols_names:
                    #     cohort_cols[pval_colname] = { "name": pval_collabel, "data": {} }
                    #     cohort_cols_names.append(pval_colname)
                    # cohort_cols[pval_colname]["data"][idx] = pvalue

            for col in cohort_cols.keys():
                if idx not in cohort_cols[col]["data"].keys():
                    cohort_cols[col]["data"][idx] = ''
                if idx != 0:
                    if missing_index not in cohort_cols[col]["data"].keys():
                        cohort_cols[col]["data"][missing_index] = ''
            idx += 1

        data.append(score_col)
        data.append(ensembl_col)
        data.append(gene_col)
        data.append(variants_nb_col)

        for colname in cohort_cols_names:
            data.append(cohort_cols[colname])

        return Response(data)


## Plots ##

class RestPlotSearch(generics.RetrieveAPIView):
    """
    Retrieve performance metrics for a given platform.
    """

    serializer_class = ScorePlotSerializer

    def get(self,request):

        queryset = Performance.objects.only('score_id','platform_id','platform__id','platform__name','publication__pmid','cohort_label').select_related('platform','publication').all().prefetch_related('performance_metric').order_by('score_id')
        params = 0

        # Search by platform
        platform = self.request.query_params.get('platform')
        if platform and platform is not None:
            queryset = queryset.filter(platform__name__iexact=platform)
            params += 1

        # Search by Publication
        pmid = self.request.query_params.get('pmid')
        if pmid and pmid is not None:
            queryset = queryset.filter(publication__pmid__iexact=pmid)
            params += 1

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
            # print(f'{idx}: {score_id}')
            score_idx[score_id] = idx
        # print(score_idx)
        # for score in queryset:
        for perf in queryset:
            perf_score_id = perf.score_id
            idx = perf_score_id
            cohort_name = perf.cohort_label
            for metric in perf.performance_metrics:
                metric_name = metric['name_short']
                metric_type = metric_name.replace(' ','')
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

        for colname in sorted(cohort_cols_names):
            data.append(cohort_cols[colname])

        return Response(data)


class RestPlotScoreSearch(generics.ListAPIView):
    """
    Retrieve the score information for the searched platform, in order to add information to the data plot (for the same platform in RestPlotSearch)
    """
    serializer_class = ScorePlotSerializer

    def get_queryset(self):
        queryset = Score.objects.select_related('publication','platform').all().prefetch_related('genes','transcripts','proteins','metabolites').order_by('num')
        params = 0

        # Search by platform
        platform = self.request.query_params.get('platform')
        if platform and platform is not None:
            queryset = queryset.filter(platform__name__iexact=platform)
            params += 1

        # Search by Publication
        pmid = self.request.query_params.get('pmid')
        if pmid and pmid is not None:
            queryset = queryset.filter(publication__pmid__iexact=pmid)
            params += 1

        if params == 0:
            queryset = []

        return queryset


##################
## Applications ##
##################
applications_db = 'applications'

class RestPhecode(generics.RetrieveAPIView):
    """
    Retrieve the Phecode information
    """

    def get(self, request, phecode_id):
        param_inc_children = self.request.query_params.get('include_children')
        try:
            queryset = Phecode.objects.using(applications_db).prefetch_related('phecode_score').get(id=phecode_id)
        except Phecode.DoesNotExist:
            queryset = None
        if (param_inc_children and str(param_inc_children)=='1'):
            serializer = PhecodeSerializerExtended(queryset,many=False)
        else:
            serializer = PhecodeSerializer(queryset,many=False)
        return Response(serializer.data)


class RestListPhecodeScore(generics.ListAPIView):
    """
    Retrieve all the Phecode Score Applications
    """
    serializer_class = ScoreApplicationsSerializer

    def get_queryset(self):
        # Fetch all the ScoresApplications
        queryset = ScoreApplications.objects.using(applications_db).select_related(*related_dict['score_applications_select']).all().prefetch_related('molecular_traits').annotate(phecode_as_float=Cast('phecode__id', output_field=FloatField()))

        # Filter data
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(score_id__iexact=filter_term) | Q(platform__name__iexact=filter_term) |
                                       Q(phecode__id__iexact=filter_term) | Q(phecode__name__icontains=filter_term) | Q(phecode__category__icontains=filter_term) |
                                       Q(molecular_traits__external_id__iexact=filter_term) | Q(molecular_traits__name__icontains=filter_term))
        # Sort data
        queryset = sort_data_list(self.request,'score_application',queryset,'phecode_as_float')
        return queryset


class RestPhecodeScore(generics.RetrieveAPIView):
    """
    Retrieve one Phecode Score Application
    """

    def get(self, request, opgs_id):
        opgs_id = opgs_id.upper()
        try:
            queryset = ScoreApplications.objects.using(applications_db).select_related(*related_dict['score_applications_select']).prefetch_related('molecular_traits').get(score_id=opgs_id)
        except ScoreApplications.DoesNotExist:
            queryset = None
        serializer = ScoreApplicationsSerializer(queryset,many=False)
        return Response(serializer.data)


class RestPhecodeScoreSearch(generics.ListAPIView):
    """
    Search the Phecode Score Application using query
    """
    serializer_class = ScoreApplicationsSerializer

    def get_queryset(self):
        queryset = ScoreApplications.objects.using(applications_db).select_related(*related_dict['score_applications_select']).prefetch_related('molecular_traits').all()
        params = 0

        # Search by Score ID
        opgs_id = self.request.query_params.get('opgs_id')
        if opgs_id and opgs_id is not None:
            opgs_id = opgs_id.upper()
            queryset = queryset.filter(score_id=opgs_id)
            params += 1
        # Search by Phecode ID
        phecode_id = self.request.query_params.get('phecode_id')
        if phecode_id and re.match('^\d+\.?\d*$',phecode_id):
            queryset = queryset.filter(phecode__id=phecode_id)
            params += 1

        # Filter data
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(score_id__iexact=filter_term) | Q(molecular_traits__external_id__iexact=filter_term) | Q(molecular_traits__name__icontains=filter_term))

        if params == 0:
            queryset = []

        return queryset


class RestListPhecodeSample(generics.ListAPIView):
    """
    Retrieve all the Phecode Sample Applications
    """
    serializer_class = SampleApplicationsSerializer

    def get_queryset(self):
        # Fetch all the ScoresApplications
        queryset = SampleApplications.objects.using(applications_db).select_related('phecode').all().annotate(phecode_as_float=Cast('phecode__id', output_field=FloatField()))

        # Filter data
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(phecode__id__iexact=filter_term) | Q(phecode__name__icontains=filter_term) | Q(phecode__category__icontains=filter_term))
        # Sort data
        queryset = sort_data_list(self.request,'sample_application',queryset,'phecode_as_float')

        return queryset