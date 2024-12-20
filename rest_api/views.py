import re, operator
from functools import reduce
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from rest_framework.serializers import ValidationError
from django.db.models import Prefetch, Q, FloatField
from django.db.models.functions import Cast, Lower
from django.conf import settings
from omicspred.models import *
from applications.models import *
from .serializers import *


generic_defer = ['curation_notes']
only_dict = {
    'scores_table': ['id','variants_number','trait_reported_id','trait_reported','dataset__name','dataset__platform__id','dataset__platform__name','dataset__publication__id','dataset__publication__pmid','dataset__publication__doi'],
    'scores_pp_table': ['id','variants_number','trait_reported_id','trait_reported','dataset__name','dataset__platform__id','dataset__platform__version','dataset__publication','ancestry'],
    'metabolite': ['id','name','external_id','pathway_group_id','pathway_subgroup_id','pathway_group__id','pathway_group__name','pathway_subgroup__id','pathway_subgroup__name']
}

defer_dict = {
    'scores_table_defer': [*generic_defer,'method_name','method_params','variants_interactions','variants_genomebuild','date_released','species','license'],
    'publication_defer': [*generic_defer,'curation_status'],
    'publication_applications': [f'publication__{x}' for x in ['doi','journal','firstauthor','authors','title','date_publication']]
}

performance_metric = [Prefetch('performance_metric', queryset=Metric.objects.only('id','performance_id','name_short','estimate').all())]
related_dict = {
    'metabolites': [Prefetch('metabolites', queryset=Metabolite.objects.only(*only_dict['metabolite']).select_related('pathway_group','pathway_subgroup').all().order_by('id'))],
    'proteins': [Prefetch('proteins', queryset=Protein.objects.only('id','name','external_id','external_id_source','description','synonyms').all().order_by('id'))],
    'genes': [Prefetch('genes', queryset=Gene.objects.only('id','name','external_id','external_id_source','synonyms','biotype','description').all().order_by('id'))],
    'molecular_traits': ['genes','transcripts','proteins','metabolites'],
    'pathway_prefetch': ['superpathways','pathway_genes','pathway_genes__gene_score','pathway_metabolites', 'pathway_metabolites__metabolite_score'],
    'performances': [Prefetch('score_performance', queryset=Performance.objects.defer('publication','efo').select_related('sample').all().prefetch_related('sample__cohorts','performance_metric').order_by('id'))],
    'performance_cohorts': [Prefetch('score_performance', queryset=Performance.objects.only('id','score_id','cohort_label','eval_type').all().prefetch_related(*performance_metric).order_by('id'))],
    'perf_select': ['score', 'sample', 'efo', 'dataset','dataset__publication','dataset__platform','dataset__platform__platform_master'],
    'dataset_select': ['platform','platform__platform_master','publication','tissue'],
    'dataset_prefetch': ['samples_training','samples_training__cohorts','samples_validation','samples_validation__cohorts'],#,'dataset_score'],
    'platform_prefetch': ['platform_version','platform_version__platform_dataset'],
    'publication_datasets': [Prefetch('datasets',queryset=Dataset.objects.select_related('platform','platform__platform_master','tissue').all().prefetch_related('samples_training','samples_training__cohorts','samples_validation','samples_validation__cohorts'))],
    'score_prefetch' : ['genes','transcripts','proteins','metabolites'],
    'score_applications_select': ['phenotype','platform','platform__platform_master','sample','cohort'],
    'score_dataset': ['dataset','dataset__publication','dataset__platform'],
    'score_dataset_full': ['dataset','dataset__publication','dataset__platform','dataset__platform__platform_master']
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
    if not sort_field or sort_field is None:
        sort_field = default_col
    # Sorting order
    is_desc = False
    if sort and sort is not None:
        if sort == 'desc':
            is_desc = True
    # Set sorting field
    if sort_field.endswith('name'):
        if is_desc == True:
            queryset = queryset.order_by(Lower(sort_field).desc())
        else:
            queryset = queryset.order_by(Lower(sort_field))
    else:
        if is_desc == True:
            sort_field = '-'+sort_field
        queryset = queryset.order_by(sort_field)
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


# Method used for the App Engine warmup
def warmup(request):
    """
    Provides default procedure for handling warmup requests on App
    Engine. Just add this view to your main urls.py.
    """
    import importlib
    from django.http import HttpResponse
    for app in settings.INSTALLED_APPS:
        for name in ('urls', 'views', 'models'):
            try:
                importlib.import_module('%s.%s' % (app, name))
            except ImportError:
                pass
    content_type = 'text/plain; charset=utf-8'
    return HttpResponse("Warmup done.", content_type=content_type)


## Cohorts ##

class RestListCohorts(generics.ListAPIView):
    """
    Retrieve all the Cohorts
    """
    serializer_class = CohortSerializerExtended

    def get_queryset(self):
        queryset = Cohort.objects.all().prefetch_related('cohorts_sample').order_by('name_short')
        ## 'filter_ids' parameter: fetch the cohorts from the list of cohort short names
        # names_list = get_ids_list(self)
        # # Filter the query depending on the parameters used
        # if names_list:
        #     names_list = r'^('+'|'.join(names_list)+')$'
        #     queryset = queryset.filter(name_short__iregex=names_list)

        return queryset

class RestCohort(generics.RetrieveAPIView):
    """
    Retrieve a Cohort
    """
    def get(self, request, cohort):
        try:
            queryset = Cohort.objects.prefetch_related('cohorts_sample').get(Q(name_short__iexact=cohort) | Q(name_full__iexact=cohort) | Q(name_others__iexact=cohort))
        except Cohort.DoesNotExist:
            queryset = None
        serializer = CohortSerializerExtended(queryset,many=False)
        return Response(serializer.data)


## Pathways ##

class RestListPathways(generics.ListAPIView):
    """
    Retrieve all the Pathways
    """
    serializer_class = PathwaySerializerExtended

    def get_queryset(self):
        # Fetch all the Pathways
        queryset = Pathway.objects.all().prefetch_related(*related_dict['pathway_prefetch']).order_by(Lower('name'))

        # Filter data - FOR PRIVATE USE CASE
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(external_id__iexact=filter_term) | Q(name__iexact=filter_term) |
                                       Q(pathway_genes__external_id__iexact=filter_term) | Q(pathway_genes__name__iexact=filter_term) |
                                       Q(pathway_metabolites__external_id__iexact=filter_term) | Q(pathway_metabolites__name__icontains=filter_term) |
                                       Q(superpathways__external_id__iexact=filter_term) | Q(superpathways__name__iexact=filter_term)).distinct()
        # Sort data
        queryset = sort_data_list(self.request,'pathway',queryset,'name')
        return queryset


class RestPathway(generics.RetrieveAPIView):
    """
    Retrieve one Pathway
    """

    def get(self, request, pathway_id):
        try:
            queryset = Pathway.objects.prefetch_related(*related_dict['pathway_prefetch']).get(Q(name__iexact=pathway_id) | Q(external_id__iexact=pathway_id))
        except Pathway.DoesNotExist:
            queryset = None
        serializer = PathwaySerializerExtended(queryset,many=False)
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
        param_extend_schema = self.request.query_params.get('extend_schema')
        try:
            queryset = Protein.objects.get(Q(name__iexact=protein_id) | Q(external_id__iexact=protein_id))
        except Protein.DoesNotExist:
            queryset = None
        if (param_extend_schema and str(param_extend_schema)=='1'):
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
        queryset = []

        # Search by Gene
        gene = self.request.query_params.get('gene')
        if gene and gene is not None:
            queryset = Protein.objects.select_related('gene').filter(Q(gene__name__iexact=gene) | Q(gene__external_id__iexact=gene)).order_by('id')

        return queryset


## Omics by platform ##

class RestMetabolomics(generics.ListAPIView):
    serializer_class = ScorePerformanceMetaboliteSerializer

    def get_queryset(self):
        # Platform
        platform = self.kwargs['platform']

        performance_metrics = self.request.query_params.get('include_performance_metrics')
        if str(performance_metrics) == '0':
            queryset = Score.objects.only(*only_dict['scores_pp_table']).select_related(*related_dict['score_dataset']).filter(dataset__platform__name__iexact=platform).prefetch_related(*related_dict['metabolites']).distinct().order_by('num')
            self.serializer_class = ScoreMetaboliteSerializer
        else:
            queryset = Score.objects.only(*only_dict['scores_pp_table']).select_related(*related_dict['score_dataset']).filter(dataset__platform__name__iexact=platform).prefetch_related(*related_dict['metabolites'],*related_dict['performance_cohorts']).distinct().order_by('num')

        ## Filters ##
        # Filter data - FOR PRIVATE USE CASE
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(id__iexact=filter_term) | Q(dataset__name__icontains=filter_term) |
                                       Q(trait_reported_id__iexact=filter_term) | Q(trait_reported__icontains=filter_term) |
                                       Q(metabolites__pathway_group__name__iexact=filter_term) | Q(metabolites__pathway_subgroup__name__iexact=filter_term) |
                                       Q(metabolites__external_id__iexact=filter_term) | Q(metabolites__name__icontains=filter_term))
        # Filter Dataset - FOR PRIVATE USE CASE
        dataset = self.request.query_params.get('dataset')
        if dataset and dataset is not None:
            queryset = queryset.filter(dataset__name=dataset)

        # Filter Publication
        pmid = self.request.query_params.get('pmid')
        if pmid and pmid is not None:
            queryset = queryset.filter(Q(dataset__publication__pmid__iexact=pmid) | Q(dataset__publication__doi__iexact=pmid))

        # Filter Version
        version = self.request.query_params.get('version')
        if version and version is not None:
            queryset = queryset.filter(dataset__platform__version=version)

        # Sort data
        queryset = sort_data_list(self.request,'score',queryset)

        return queryset


class RestProteomics(generics.ListAPIView):
    serializer_class = ScorePerformanceProteinSerializer

    def get_queryset(self):
        # Platform
        platform = self.kwargs['platform']

        performance_metrics = self.request.query_params.get('include_performance_metrics')
        if str(performance_metrics) == '0':
            queryset = Score.objects.only(*only_dict['scores_pp_table']).select_related(*related_dict['score_dataset']).filter(dataset__platform__name__iexact=platform).prefetch_related(*related_dict['proteins'],*related_dict['genes']).distinct()
            self.serializer_class = ScoreProteinSerializer
        else:
            queryset = Score.objects.only(*only_dict['scores_pp_table']).select_related(*related_dict['score_dataset']).filter(dataset__platform__name__iexact=platform).prefetch_related(*related_dict['proteins'],*related_dict['genes'],*related_dict['performance_cohorts']).distinct()

        ## Filters ##
        # Filter data - FOR PRIVATE USE CASE
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(id__iexact=filter_term) | Q(dataset__name__icontains=filter_term) |
                                       Q(dataset__platform__version__icontains=filter_term) |
                                       Q(proteins__external_id__iexact=filter_term) | Q(proteins__name__icontains=filter_term) |
                                       Q(genes__external_id__iexact=filter_term) | Q(genes__name__iexact=filter_term))
        # Filter Dataset - FOR PRIVATE USE CASE
        dataset = self.request.query_params.get('dataset')
        if dataset and dataset is not None:
            queryset = queryset.filter(dataset__name=dataset)

        # Filter platform versions - FOR PRIVATE USE CASE
        platform_versions = self.request.query_params.get('versions')
        if platform_versions and platform_versions is not None:
            platform_versions_list = platform_versions.split(';')
            queryset = queryset.filter(dataset__platform__version__in=platform_versions_list)

        # Filter Ancestry - FOR PRIVATE USE CASE
        ancestry = self.request.query_params.get('anc')
        if ancestry and ancestry is not None:
            anc_training_filter = Q(**{f'ancestry__dev__anc__{ancestry}__isnull':False})
            anc_validation_filter = Q(**{f'ancestry__eval__anc__{ancestry}__isnull':False})
            stage = self.request.query_params.get('stage')
            match stage:
                case 't': # Training
                    queryset = queryset.filter(anc_training_filter)
                case 'v': # Validation
                    queryset = queryset.filter(anc_validation_filter)
                case 'b': # Training and Validation
                    queryset = queryset.filter(anc_training_filter & anc_validation_filter)
                case _: # No stage provided
                    queryset = queryset.filter(anc_training_filter | anc_validation_filter)

        # Filter Publication
        pmid = self.request.query_params.get('pmid')
        if pmid and pmid is not None:
            queryset = queryset.filter(Q(dataset__publication__pmid__iexact=pmid) | Q(dataset__publication__doi__iexact=pmid))

        # Filter Version
        version = self.request.query_params.get('version')
        if version and version is not None:
            queryset = queryset.filter(dataset__platform__version=version)

        # Sort data
        queryset = sort_data_list(self.request,'score',queryset)

        return queryset


class RestTranscriptomics(generics.ListAPIView):
    serializer_class = ScorePerformanceTranscriptSerializer

    def get_queryset(self):
        # Platform
        platform = self.kwargs['platform']

        performance_metrics = self.request.query_params.get('include_performance_metrics')
        if str(performance_metrics) == '0':
            queryset = Score.objects.only(*only_dict['scores_pp_table']).select_related(*related_dict['score_dataset']).filter(dataset__platform__name__iexact=platform).prefetch_related(*related_dict['genes']).distinct().order_by('num')
            self.serializer_class = ScoreTranscriptSerializer
        else:
            queryset = Score.objects.only(*only_dict['scores_pp_table']).select_related(*related_dict['score_dataset']).filter(dataset__platform__name__iexact=platform).prefetch_related(*related_dict['genes'],*related_dict['performance_cohorts']).distinct().order_by('num')

        ## Filters ##
        # Filter data - FOR PRIVATE USE CASE
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(id__iexact=filter_term) | Q(dataset__name__icontains=filter_term) |
                                       Q(genes__external_id__iexact=filter_term) | Q(genes__name__iexact=filter_term))
        # Filter Dataset - FOR PRIVATE USE CASE
        dataset = self.request.query_params.get('dataset')
        if dataset and dataset is not None:
            queryset = queryset.filter(dataset__name=dataset)

        # Filter Publication
        pmid = self.request.query_params.get('pmid')
        if pmid and pmid is not None:
            queryset = queryset.filter(Q(dataset__publication__pmid__iexact=pmid) | Q(dataset__publication__doi__iexact=pmid))

        # Filter Version
        version = self.request.query_params.get('version')
        if version and version is not None:
            queryset = queryset.filter(dataset__platform__version=version)

        # Sort data
        queryset = sort_data_list(self.request,'score',queryset)

        return queryset


## Performance metrics ##

# class RestListPerformances(generics.ListAPIView):
#     """
#     Retrieve all the Performance Metrics
#     """
#     queryset = Performance.objects.select_related(*related_dict['perf_select']).all().prefetch_related('sample__cohorts','performance_metric').order_by('id')
#     serializer_class = PerformanceSerializer


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
            queryset = queryset.filter(dataset__publication__pmid=pmid)
            params += 1

        # Search by Gene
        gene = self.request.query_params.get('gene')
        if gene and gene is not None:
            queryset = queryset.filter(Q(score__genes__external_id__iexact=gene) | Q(score__genes__name__iexact=gene)).prefetch_related('score__genes')
            params += 1

        # Search by Protein
        protein = self.request.query_params.get('protein')
        if protein and protein is not None:
            queryset = queryset.filter(Q(score__proteins__external_id__iexact=protein) | Q(score__proteins__name__iexact=protein)).prefetch_related('score__proteins')
            params += 1

        # Search by Metabolite
        metabolite = self.request.query_params.get('metabolite')
        if metabolite and metabolite is not None:
            queryset = queryset.filter(Q(score__metabolites__external_id__iexact=metabolite) | Q(score__metabolites__name__iexact=metabolite)).prefetch_related('score__metabolites')
            params += 1

        # Search by Platform
        platform = self.request.query_params.get('platform')
        if platform and platform is not None:
            queryset = queryset.filter(dataset__platform__name=platform)
            params += 1

        if params == 0:
            queryset = []

        return queryset



class RestPerformanceSearchByMolecularTrait(generics.ListAPIView):
    """
    Search the Performance metric(s) using molecular trait name/id
    """
    serializer_class = PerformanceSerializer

    def get_queryset(self):
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
            opgs_id = self.request.query_params.get('opgs_id')
            if opgs_id and opgs_id is not None:
                opgs_id = opgs_id.upper()
                queryset = queryset.filter(score__id=opgs_id)

            # Search by PubMed ID
            pmid = self.request.query_params.get('pmid')
            if pmid and pmid.isnumeric():
                queryset = queryset.filter(publication__pmid=pmid)

            # Search by Platform
            platform = self.request.query_params.get('platform')
            if platform and platform is not None:
                queryset = queryset.filter(platform__name=platform)

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
        except PlatformMaster.DoesNotExist:
            queryset = None
        serializer = PlatformMasterSerializer(queryset,many=False)
        return Response(serializer.data)


class RestListDatasets(generics.ListAPIView):
    """
    Retrieve all the Dataset
    """
    serializer_class = DatasetSerializer
    queryset = Dataset.objects.select_related(*related_dict['dataset_select']).all().prefetch_related(*related_dict['dataset_prefetch'])


class RestDataset(generics.ListAPIView):
    """
    Retrieve the Dataset information from a given platform
    """
    serializer_class = DatasetSerializer

    def get_queryset(self):
        try:
            dataset = self.kwargs['dataset']
            # Database filtering
            queryset = Dataset.objects.select_related(*related_dict['dataset_select']).prefetch_related(*related_dict['dataset_prefetch']).filter(name__iexact=dataset)
            # Filter by publication
            pmid = self.request.query_params.get('pmid')
            if pmid and pmid.isnumeric():
                queryset = queryset.filter(publication__pmid=pmid)
            # Filter by platform
            platform = self.request.query_params.get('platform')
            if platform and platform is not None:
                queryset = queryset.filter(platform__name__iexact=platform)
        except Dataset.DoesNotExist:
            queryset = []
        return queryset


class RestDatasetSearch(generics.ListAPIView):
    """
    Retrieve the Dataset information from a given platform and/or PubMed ID
    """
    serializer_class = DatasetSerializer

    def get_queryset(self):
        try:
            # Database filtering
            queryset = Dataset.objects.select_related(*related_dict['dataset_select']).prefetch_related(*related_dict['dataset_prefetch']).all()
            # Filter by publication
            pmid = self.request.query_params.get('pmid')
            if pmid and pmid.isnumeric():
                queryset = queryset.filter(publication__pmid=pmid)
            # Filter by platform
            platform = self.request.query_params.get('platform')
            if platform and platform is not None:
                queryset = queryset.filter(platform__name__iexact=platform)
        except Dataset.DoesNotExist:
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
        queryset = Publication.objects.defer(*defer_dict['publication_defer']).all().prefetch_related(*related_dict['publication_datasets']).order_by('id')
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
            queryset = Publication.objects.defer(*defer_dict['publication_defer']).prefetch_related(*related_dict['publication_datasets']).get(pmid__iexact=pmid)
            # queryset = Publication.objects.defer(*defer_dict['publication_defer']).prefetch_related('platforms','platforms__platform__platform_master','platforms__tissue','platforms__samples_training','platforms__samples_training__cohorts','platforms__samples_validation','platforms__samples_validation__cohorts').get(pmid__iexact=pmid)
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
        # queryset = Publication.objects.defer(*defer_dict['publication_defer']).all().order_by('id')
        queryset = Publication.objects.defer(*defer_dict['publication_defer']).all().prefetch_related(*related_dict['publication_datasets']).order_by('id')

        params = 0

        # Search by Score ID
        pgs_id = self.request.query_params.get('opgs_id')
        if pgs_id and pgs_id is not None:
            pgs_id = pgs_id.upper()
            try:
                score = Score.objects.only('id','dataset__publication__id').select_related('dataset','dataset__publication').get(id=pgs_id)
                queryset = queryset.filter(id=score.dataset.publication.id)
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
    Retrieve the Genetic Scores
    """
    serializer_class = ScoreLightSerializer

    def get_queryset(self):
        include_ancestry = self.request.query_params.get('include_ancestry')
        # Fetch all the Scores
        if include_ancestry and str(include_ancestry) == '1':
            self.serializer_class = ScoreSerializer
        else:
            self.serializer_class = ScoreLightSerializer
        queryset = Score.objects.select_related(*related_dict['score_dataset_full']).all().prefetch_related(*related_dict['score_prefetch']).order_by('num')

        # Filter by list of Score IDs
        ids_list = get_ids_list(self)
        if ids_list:
            queryset = queryset.filter(id__in=ids_list)

        # Filter data - FOR PRIVATE USE CASE
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(id__iexact=filter_term) | Q(name__iexact=filter_term) |
                                       Q(genes__external_id__iexact=filter_term) | Q(genes__name__iexact=filter_term) |
                                       Q(proteins__external_id__iexact=filter_term) | Q(proteins__name__icontains=filter_term) |
                                       Q(metabolites__external_id__iexact=filter_term) | Q(metabolites__name__icontains=filter_term) |
                                       Q(dataset__platform__name__iexact=filter_term) | Q(dataset__platform__platform_master__type__iexact=filter_term) | 
                                       Q(dataset__publication__firstauthor__iexact=filter_term))
         # Sort data
        queryset = sort_data_list(self.request,'score',queryset)
        return queryset


class RestScore(generics.RetrieveAPIView):
    """
    Retrieve one Genetic Score
    """

    def get(self, request, opgs_id):
        opgs_id = opgs_id.upper()
        include_pathway = self.request.query_params.get('include_pathway')
        try:
            if include_pathway and str(include_pathway)=='1':
                queryset = Score.objects.select_related(*related_dict['score_dataset_full']).prefetch_related('genes__pathways','genes__pathways__superpathways','metabolites__pathways','metabolites__pathways__superpathways').get(id=opgs_id)
            else:
                queryset = Score.objects.select_related(*related_dict['score_dataset_full']).get(id=opgs_id)
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
            include_performance_metrics = self.request.query_params.get('include_performance_metrics')
            include_performance_data = self.request.query_params.get('include_performance_data')
            # Add the performance metrics data structure
            if include_performance_metrics and str(include_performance_metrics) == '1':
                self.serializer_class = ScorePerformanceSerializer
                queryset = Score.objects.select_related(*related_dict['score_dataset_full']).filter(reduce(operator.or_,query_list)).prefetch_related(*related_dict['molecular_traits'],'score_performance','score_performance__sample','score_performance__sample__cohorts','score_performance__performance_metric').distinct().order_by('num')
            # Add the performance metrics condensed data (for web display on tables) - PRIVATE parameter
            elif include_performance_data and str(include_performance_data) == '1':
                self.serializer_class = ScorePerformanceDataSerializer
                queryset = Score.objects.select_related(*related_dict['score_dataset_full']).filter(reduce(operator.or_,query_list)).prefetch_related(*related_dict['molecular_traits'],*related_dict['performance_cohorts']).distinct().order_by('num')
            # Metadata without performance metrics information - PUBLIC parameter
            else:
                queryset = Score.objects.select_related(*related_dict['score_dataset_full']).filter(reduce(operator.or_,query_list)).prefetch_related(*related_dict['molecular_traits']).distinct().order_by('num')

        return queryset


class RestScoreSearch(generics.ListAPIView):
    """
    Search the Genetic Score(s) using query
    """

    def get_queryset(self):
        include_ancestry = self.request.query_params.get('include_ancestry')
        # Fetch all the Scores
        if str(include_ancestry) == '0':
            self.serializer_class = ScoreLightSerializer
        else:
            self.serializer_class = ScoreSerializer
        queryset = Score.objects.select_related(*related_dict['score_dataset_full']).all().prefetch_related(*related_dict['molecular_traits']).order_by('num')
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
            queryset = queryset.filter(dataset__publication__pmid=pmid)
            params += 1

        # Search by platform
        platform = self.request.query_params.get('platform')
        if platform and platform is not None:
            queryset = queryset.filter(dataset__platform__name__iexact=platform)
            params += 1

        # Search by Cohort
        cohort = self.request.query_params.get('cohort')
        if cohort and cohort is not None:
            # queryset = queryset.filter(dataset__platform__name__iexact=platform)
            queryset = queryset.filter(score_performance__sample__cohorts__name_short__iexact=cohort).prefetch_related('score_performance', 'score_performance__sample', 'score_performance__sample__cohorts')
            params += 1


        # Filter data - FOR PRIVATE USE CASE
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(id__iexact=filter_term) |
                                       Q(genes__external_id__iexact=filter_term) | Q(genes__name__icontains=filter_term) |
                                       Q(proteins__external_id__iexact=filter_term) | Q(proteins__name__icontains=filter_term) |
                                       Q(metabolites__external_id__iexact=filter_term) | Q(metabolites__name__icontains=filter_term) |
                                       Q(dataset__platform__name__iexact=filter_term) | Q(dataset__platform__platform_master__type__iexact=filter_term))

        if params == 0:
            queryset = []
        else:
            queryset = queryset.distinct()

        # Avoid duplicated entries when a cohort is used several times for a score (with different ancestries/samples)
        return queryset


## Tables - format by column ##

# class RestTableSearch(generics.ListAPIView):
#     serializer_class = ScoreExtendedSerializer

#     def get_queryset(self):
#         queryset = Score.objects.select_related('publication','platform').all().order_by('num')
#         params = 0

#         # Search by platform
#         platform = self.request.query_params.get('platform')
#         if platform and platform is not None:
#             queryset = queryset.filter(platform__name__iexact=platform)
#             params += 1

#         if params == 0:
#             queryset = []

#         return queryset


# class RestMetaboliteTableSearch(generics.RetrieveAPIView):

#     def get(self,request):
#         #queryset = Score.objects.select_related('platform').all().prefetch_related('metabolites').order_by('num')
#         queryset = Score.objects.only(*only_dict['scores_table']).select_related('platform').all().prefetch_related(*related_dict['performances'],*related_dict['metabolites']).order_by('num')

#         # Search by platform
#         platform = self.request.query_params.get('platform')
#         if platform and platform is not None:
#             queryset = queryset.filter(platform__name__iexact=platform)
#         else:
#             queryset = []

#         data = []
#         score_col = { "name": "OMICSPRED ID", "data": {} }

#         if platform == 'Metabolon':
#             metabolon_col = { "name": "Metabolon ID", "data": {} }
#         else:
#             metabolon_col = None

#         metabo_col = { "name": "Biochemical Name", "data": {} }
#         pathway_grp_col = { "name": "Pathway Group", "data": {} }
#         pathway_subgrp_col = { "name": "Pathway Subgroup", "data": {} }
#         variants_nb_col = { "name": "#SNP", "data": {} }
#         cohort_cols = {}
#         cohort_cols_names = []

#         idx = 0
#         for score in queryset:
#             # OMICPRED ID
#             score_col["data"][idx] = score.id

#             # Metabolite Information
#             metabolite = score.metabolites.all()[0]
#             # - Metabolon ID
#             if metabolon_col:
#                 metabolon_col["data"][idx] = metabolite.external_id
#             # - Biochemical Name
#             metabo_col["data"][idx] = metabolite.name
#             # - Pathway Group
#             pathway_group = None
#             if metabolite.pathway_group:
#                 pathway_group = metabolite.pathway_group.name
#             pathway_grp_col["data"][idx] = pathway_group
#             # - Pathway Subgroup
#             pathway_subgroup = None
#             if metabolite.pathway_subgroup:
#                 pathway_subgroup = metabolite.pathway_subgroup.name
#             pathway_subgrp_col["data"][idx] = pathway_subgroup

#             # #SNP
#             variants_nb_col["data"][idx] = score.variants_number

#             for perf in score.score_performance.all():
#                 cohort_name = perf.sample.cohorts.all()[0].name_short
#                 for metric in perf.performance_metrics:
#                     metric_name = metric['name_short']
#                     if 'estimate' in metric.keys():
#                         estimate = metric['estimate']
#                     else:
#                         estimate = ''

#                     colname = f'{cohort_name}_{metric_name}'
#                     collabel = f'{cohort_name} {metric_name}'
#                     # Cohort estimate
#                     if colname not in cohort_cols_names:
#                         cohort_cols[colname] = { "name": collabel, "data": {} }
#                         cohort_cols_names.append(colname)
#                     cohort_cols[colname]["data"][idx] = estimate
#                     # Cohort pvalue
#                     # if 'pvalue' in metric.keys():
#                     #     pvalue = metric['pvalue']
#                     # else:
#                     #     pvalue = ''
#                     # pval_colname = f'{colname}_pvalue'
#                     # pval_collabel = f'{colname} (p-value)'
#                     # if pval_colname not in cohort_cols_names:
#                     #     cohort_cols[pval_colname] = { "name": pval_collabel, "data": {} }
#                     #     cohort_cols_names.append(pval_colname)
#                     # cohort_cols[pval_colname]["data"][idx] = pvalue
#             for col in cohort_cols.keys():
#                 if idx not in cohort_cols[col]["data"].keys():
#                     cohort_cols[col]["data"][idx] = ''
#                 if idx != 0:
#                     if missing_index not in cohort_cols[col]["data"].keys():
#                         cohort_cols[col]["data"][missing_index] = ''
#             idx += 1

#         data.append(score_col)
#         if metabolon_col:
#             data.append(metabolon_col)
#         data.append(metabo_col)
#         data.append(pathway_grp_col)
#         data.append(pathway_subgrp_col)
#         data.append(variants_nb_col)

#         for colname in cohort_cols_names:
#             data.append(cohort_cols[colname])

#         return Response(data)


# class RestProteinTableSearch(generics.RetrieveAPIView):
#     def get(self,request):
#         queryset = Score.objects.only(*only_dict['scores_table']).select_related('platform').all().prefetch_related(*related_dict['performances'],*related_dict['genes'],*related_dict['proteins']).order_by('num')

#         # Search by platform
#         platform = self.request.query_params.get('platform')
#         if platform and platform is not None:
#             queryset = queryset.filter(platform__name__iexact=platform)
#         else:
#             queryset = []

#         data = []
#         score_col = { "name": "OMICSPRED ID", "data": {} }

#         if platform == 'Somalogic':
#             somascan_col = { "name": "SOMAscan ID", "data": {} }
#         else:
#             somascan_col = None

#         uniprot_col = { "name": "UniProt ID", "data": {} }
#         gene_col = { "name": "Gene", "data": {} }
#         protein_col = { "name": "Protein", "data": {} }
#         variants_nb_col = { "name": "#SNP", "data": {} }
#         cohort_cols = {}
#         cohort_cols_names = []

#         idx = 0
#         for score in queryset:
#             # idx = f'"{idx}"'
#             # OMICPRED ID
#             score_col["data"][idx] = score.id
#             # SOMAscan ID
#             if somascan_col:
#                 somascan_col["data"][idx] = score.name

#             # Protein Information
#             # Sorting later instead of using the queryset method "order_by" to avoid generating more SQL queries
#             proteins = [x for x in score.proteins.all()]
#             # - UniProt ID(s)
#             uniprot_ids = set()
#             for protein_id in sorted([x.external_id for x in proteins]):
#                 if protein_id:
#                     uniprot_ids.add(protein_id)
#             uniprot_col["data"][idx] = ';'.join(uniprot_ids)
#             # - Protein name(s)
#             protein_names = set()
#             for protein_name in sorted([x.name for x in proteins]):
#                 if protein_name:
#                     protein_names.add(protein_name)
#             protein_col["data"][idx] = ';'.join(protein_names)

#             # Gene informatiom
#             gene_names = set()
#             # Sorting later instead of using the queryset method "order_by" to avoid generating more SQL queries
#             for gene_name in sorted([x.name for x in score.genes.all()]):
#                 if gene_name:
#                     gene_names.add(gene_name)
#             gene_col["data"][idx] = ';'.join(gene_names)

#             # #SNP
#             variants_nb_col["data"][idx] = score.variants_number

#             for perf in score.score_performance.all():
#                 cohort_name = perf.sample.cohorts.all()[0].name_short
#                 for metric in perf.performance_metrics:
#                     metric_name = metric['name_short']
#                     if 'estimate' in metric.keys():
#                         estimate = metric['estimate']
#                     else:
#                         estimate = ''

#                     colname = f'{cohort_name}_{metric_name}'
#                     collabel = f'{cohort_name} {metric_name}'
#                     # Cohort estimate
#                     if colname not in cohort_cols_names:
#                         cohort_cols[colname] = { "name": collabel, "data": {} }
#                         cohort_cols_names.append(colname)
#                     cohort_cols[colname]["data"][idx] = estimate
#             #         # Cohort pvalue
#             #         # if 'pvalue' in metric.keys():
#             #         #     pvalue = metric['pvalue']
#             #         # else:
#             #         #     pvalue = ''
#             #         # pval_colname = f'{colname}_pvalue'
#             #         # pval_collabel = f'{colname} (p-value)'
#             #         # if pval_colname not in cohort_cols_names:
#             #         #     cohort_cols[pval_colname] = { "name": pval_collabel, "data": {} }
#             #         #     cohort_cols_names.append(pval_colname)
#             #         # cohort_cols[pval_colname]["data"][idx] = pvalue
#             for col in cohort_cols.keys():
#                 if idx not in cohort_cols[col]["data"].keys():
#                     cohort_cols[col]["data"][idx] = ''
#                 if idx != 0:
#                     if missing_index not in cohort_cols[col]["data"].keys():
#                         cohort_cols[col]["data"][missing_index] = ''
#             idx += 1

#         data.append(score_col)
#         if somascan_col:
#             data.append(somascan_col)
#         data.append(uniprot_col)
#         data.append(gene_col)
#         data.append(protein_col)
#         data.append(variants_nb_col)

#         for colname in cohort_cols_names:
#             data.append(cohort_cols[colname])

#         return Response(data)


# class RestTranscriptTableSearch(generics.RetrieveAPIView):

#     def get(self,request):
#         # queryset = Score.objects.select_related('platform').all().prefetch_related('genes').order_by('num')
#         queryset = Score.objects.only(*only_dict['scores_table']).select_related('platform').all().prefetch_related(*related_dict['performances'],*related_dict['genes_sources']).order_by('num') # transcripts

#         # Search by platform
#         platform = self.request.query_params.get('platform')
#         if platform and platform is not None:
#             queryset = queryset.filter(platform__name__iexact=platform)
#         else:
#             queryset = []

#         data = []
#         score_col = { "name": "OMICSPRED ID", "data": {} }

#         ensembl_col = { "name": "Ensembl ID", "data": {} }
#         gene_col = { "name": "Gene", "data": {} }
#         # transcript_col = { "name": "Transcript", "data": {} }
#         variants_nb_col = { "name": "#SNP", "data": {} }
#         cohort_cols = {}
#         cohort_cols_names = []

#         idx = 0
#         for score in queryset:
#             # idx = f"{idx}"
#             # OMICPRED ID
#             score_col["data"][idx] = score.id

#             # Gene informatiom
#             ensembl_ids = set()
#             gene_names = set()
#             # Sorting later instead of using the queryset method "order_by" to avoid generating more SQL queries
#             genes = score.genes.all()
#             for gene in sorted(genes, key=lambda x: x.name):
#                 if gene.external_id and gene.external_id_source == 'Ensembl':
#                         ensembl_ids.add(gene.external_id)
#                 if gene.name:
#                     gene_names.add(gene.name)
#             ensembl_col["data"][idx] = ';'.join(ensembl_ids)
#             gene_col["data"][idx] = ';'.join(gene_names)

#             # # Transcript informatiom
#             # transcript_names = set()
#             # for transcript in score.transcripts.all().order_by('name'):
#             #     if transcript.name:
#             #         transcript_names.add(transcript.name)
#             # transcript_col["data"][idx] = ';'.join(transcript_names)
#             # #SNP
#             variants_nb_col["data"][idx] = score.variants_number

#             for perf in score.score_performance.all():
#                 cohort_name = perf.sample.cohorts.all()[0].name_short
#                 for metric in perf.performance_metrics:
#                     metric_name = metric['name_short']
#                     if 'estimate' in metric.keys():
#                         estimate = metric['estimate']
#                     else:
#                         estimate = ''

#                     colname = f'{cohort_name}_{metric_name}'
#                     collabel = f'{cohort_name} {metric_name}'
#                     # Cohort estimate
#                     if colname not in cohort_cols_names:
#                         cohort_cols[colname] = { "name": collabel, "data": {} }
#                         cohort_cols_names.append(colname)
#                     cohort_cols[colname]["data"][idx] = estimate

#                     # Cohort pvalue
#                     # if 'pvalue' in metric.keys():
#                     #     pvalue = metric['pvalue']
#                     # else:
#                     #     pvalue = ''
#                     # pval_colname = f'{colname}_pvalue'
#                     # pval_collabel = f'{colname} (p-value)'
#                     # if pval_colname not in cohort_cols_names:
#                     #     cohort_cols[pval_colname] = { "name": pval_collabel, "data": {} }
#                     #     cohort_cols_names.append(pval_colname)
#                     # cohort_cols[pval_colname]["data"][idx] = pvalue

#             for col in cohort_cols.keys():
#                 if idx not in cohort_cols[col]["data"].keys():
#                     cohort_cols[col]["data"][idx] = ''
#                 if idx != 0:
#                     if missing_index not in cohort_cols[col]["data"].keys():
#                         cohort_cols[col]["data"][missing_index] = ''
#             idx += 1

#         data.append(score_col)
#         data.append(ensembl_col)
#         data.append(gene_col)
#         data.append(variants_nb_col)

#         for colname in cohort_cols_names:
#             data.append(cohort_cols[colname])

#         return Response(data)


## Plots ##
from plot.models import Plot
class RestPlotSearch(generics.ListAPIView):

    serializer_class = PlotSerializer

    def get_queryset(self):
        queryset = Plot.objects.using('plot').all()
        params = 0

        # Search by Pubmed ID
        pmid = self.request.query_params.get('pmid')
        if pmid and pmid.isnumeric():
            queryset = queryset.filter(pmid=pmid)
            params += 1

        # Search by platform
        platform = self.request.query_params.get('platform')
        if platform and platform is not None:
            queryset = queryset.filter(platform_name__iexact=platform)
            params += 1

        # Search by dataset
        dataset = self.request.query_params.get('dataset')
        if dataset and dataset is not None:
            queryset = queryset.filter(dataset_name__iexact=dataset)
            params += 1

        if params == 0:
            queryset = []

        return queryset


class RestPlotFileSearch(generics.RetrieveAPIView):
    """
    Retrieve performance metrics for a given platform.
    """

    serializer_class = ScorePlotSerializer

    def get(self,request):

        queryset = Performance.objects.only('score_id','dataset__id','dataset__platform__id','dataset__platform__name','dataset__publication__pmid','eval_type','cohort_label').select_related('dataset','dataset__publication','dataset__platform').all().prefetch_related('performance_metric').order_by('score_id')
        params = 0

        # Search by platform
        platform = self.request.query_params.get('platform')
        if platform and platform is not None:
            queryset = queryset.filter(dataset__platform__name__iexact=platform)
            params += 1

        # Search by Publication
        pmid = self.request.query_params.get('pmid')
        if pmid and pmid.isnumeric():
            queryset = queryset.filter(dataset__publication__pmid__iexact=pmid)
            params += 1

        # Search by Dataset
        dataset = self.request.query_params.get('dataset')
        if dataset and dataset is not None:
            queryset = queryset.filter(dataset__name=dataset)
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
    """
    serializer_class = ScorePlotSerializer

    def get_queryset(self):
        queryset = Score.objects.select_related(*related_dict['score_dataset_full']).all().prefetch_related('genes','transcripts','proteins','metabolites').order_by('num')
        params = 0

        # Search by platform
        platform = self.request.query_params.get('platform')
        if platform and platform is not None:
            queryset = queryset.filter(dataset__platform__name__iexact=platform)
            params += 1

        # Search by Publication
        pmid = self.request.query_params.get('pmid')
        if pmid and pmid.isnumeric():
            queryset = queryset.filter(dataset__publication__pmid__iexact=pmid)
            params += 1

        # Search by Dataset
        dataset = self.request.query_params.get('dataset')
        if dataset and dataset is not None:
            queryset = queryset.filter(dataset__name=dataset)
            params += 1

        if params == 0:
            queryset = []

        return queryset


##################
## Applications ##
##################
applications_db = 'applications'

class RestPhenotype(generics.RetrieveAPIView):
    """
    Retrieve the Phenotype information
    """

    def get(self, request, phenotype_id):
        param_inc_children = self.request.query_params.get('include_children')
        try:
            queryset = Phenotype.objects.using(applications_db).prefetch_related('phenotype_score').get(id=phenotype_id)
        except Phenotype.DoesNotExist:
            queryset = None
        if (param_inc_children and str(param_inc_children)=='1'):
            serializer = PhenotypeSerializerExtended(queryset,many=False)
        else:
            serializer = PhenotypeSerializerScoresCount(queryset,many=False)
        return Response(serializer.data)


class RestListPhenotypeScore(generics.ListAPIView):
    """
    Retrieve all the Phenotype Score Applications
    """
    serializer_class = ScoreApplicationsSerializer

    def get_queryset(self):
        # Fetch all the ScoresApplications
        queryset = ScoreApplications.objects.using(applications_db).select_related(*related_dict['score_applications_select']).all().prefetch_related('molecular_traits').annotate(phenotype_as_float=Cast('phenotype__id', output_field=FloatField()))

        # Filter by list of Score IDs
        ids_list = get_ids_list(self)
        if ids_list:
            queryset = queryset.filter(score_id__in=ids_list)

        # Filter data - FOR PRIVATE USE CASE
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(score_id__iexact=filter_term) | Q(platform__name__iexact=filter_term) | Q(platform__platform_master__type__iexact=filter_term) |
                                       Q(phenotype__id__iexact=filter_term) | Q(phenotype__name__icontains=filter_term) | Q(phenotype__category__icontains=filter_term) |
                                       Q(cohort__name_short__iexact=filter_term) | Q(cohort__name_full__iexact=filter_term) |
                                       Q(molecular_traits__external_id__iexact=filter_term) | Q(molecular_traits__name__icontains=filter_term))
        # Sort data
        queryset = sort_data_list(self.request,'score_application',queryset,'phenotype_as_float')
        return queryset.distinct()


class RestPhenotypeScore(generics.ListAPIView):
    """
    Retrieve all the Phenotype Score Application for a given Score ID
    """

    serializer_class = ScoreApplicationsSerializer

    def get_queryset(self):
        opgs_id = self.kwargs['opgs_id'].upper()
        queryset = ScoreApplications.objects.using(applications_db).select_related(*related_dict['score_applications_select']).prefetch_related('molecular_traits').filter(score_id=opgs_id)
        return queryset


class RestPhenotypeScoreSearch(generics.ListAPIView):
    """
    Search the Phenotype Score Application using query
    """
    serializer_class = ScoreApplicationsSerializer

    def get_queryset(self):
        queryset = ScoreApplications.objects.using(applications_db).defer(*defer_dict['publication_applications']).select_related(*related_dict['score_applications_select'],'publication').prefetch_related('molecular_traits').all()
        params = 0

        # Search by Score ID
        opgs_id = self.request.query_params.get('opgs_id')
        if opgs_id and opgs_id is not None:
            opgs_id = opgs_id.upper()
            queryset = queryset.filter(score_id=opgs_id)
            params += 1
        # Search by PubMed ID
        pmid = self.request.query_params.get('pmid')
        if pmid and pmid.isnumeric():
            queryset = queryset.filter(publication__pmid=pmid)
            params += 1
        # Search by Phenotype ID
        phenotype_id = self.request.query_params.get('phenotype_id')
        if phenotype_id and re.match(r'^\d+\.?\d*$',phenotype_id):
            queryset = queryset.filter(phenotype__id=phenotype_id)
            params += 1
        # Search by Phenotype ID
        molecular_trait_id = self.request.query_params.get('molecular_trait_id')
        if molecular_trait_id and molecular_trait_id is not None:
            queryset = queryset.filter(Q(molecular_traits__name__iexact=molecular_trait_id) | Q(molecular_traits__external_id__iexact=molecular_trait_id))
            params += 1

        # Filter data - FOR PRIVATE USE CASE
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(score_id__iexact=filter_term) | Q(molecular_traits__external_id__iexact=filter_term) | Q(molecular_traits__name__icontains=filter_term))

        if params == 0:
            queryset = []

        return queryset


class RestListPhenotypeSample(generics.ListAPIView):
    """
    Retrieve all the Phenotype Sample Applications
    """
    serializer_class = SampleApplicationsLegacySerializer

    def get_queryset(self):
        # Fetch all the ScoresApplications
        queryset = SampleApplicationsLegacy.objects.using(applications_db).select_related('phenotype',).all().prefetch_related('phenotype__phenotype_score').annotate(phenotype_as_float=Cast('phenotype__id', output_field=FloatField()))

        # Filter by list of PheCode IDs
        ids_list = get_ids_list(self)
        if ids_list:
            queryset = queryset.filter(phenotype__id__in=ids_list)

        # Filter data - FOR PRIVATE USE CASE
        filter_term = self.request.query_params.get('filter')
        if filter_term and filter_term is not None:
            queryset = queryset.filter(Q(phenotype__id__iexact=filter_term) | Q(phenotype__name__icontains=filter_term) | Q(phenotype__category__icontains=filter_term))
        # Sort data
        queryset = sort_data_list(self.request,'sample_application',queryset,'phenotype_as_float')

        return queryset


class RestInfo(generics.RetrieveAPIView):
    """
    Return diverse information related to the REST API and the PGS Catalog
    """

    def get(self, request):

        data = {
            'rest_api': {
                "version": "1.0"
            },
            'data_count': {
                'scores': Score.objects.count(),
                'publications': Publication.objects.count(),
                'platforms': PlatformMaster.objects.count(),
                'pathways': Pathway.objects.count(),
                'phenotypes': Phenotype.objects.using(applications_db).count(),
                'phenotype_associations': ScoreApplications.objects.using(applications_db).count(),
                'tissues': EFO.objects.filter(type='tissue').count()
            }
        }

        return Response(data)