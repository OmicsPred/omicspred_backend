import operator
from functools import reduce

from django.conf import settings
from django.db.models import Count, Prefetch, Q
# from django.db.models.functions import Lower
from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import exception_handler

from omicspred.models import *
from ..query_utils import *
from ..serializers import *

dataset_publication = [
    'dataset__publication__id', 'dataset__publication__title', 'dataset__publication__doi',
    'dataset__publication__journal', 'dataset__publication__firstauthor', 'dataset__publication__pmid',
    'dataset__publication__date_publication'
]
score_cols_base = ['id', 'name', 'variants_number', 'trait_reported_id', 'trait_reported']
tissue_cols_base = ['dataset__tissue__id', 'dataset__tissue__label', 'dataset__tissue__description', 'dataset__tissue__url', 'dataset__tissue__type']

only_dict = {
    'score': [
        *score_cols_base,
        'method_name', 'method_params',
        'dataset__id', 'dataset__name',
        'dataset__publication_id', *dataset_publication,
        'dataset__platform__name', 'dataset__platform__version',
        'dataset__platform__platform_master__type', 'dataset__platform__platform_master__full_name',
        'dataset__platform__platform_master__technique',
        *tissue_cols_base,
        'variants_interactions', 'variants_genomebuild',
        'comment', 'license',
    ],
    'score_website': [
        *score_cols_base,
        'dataset__id', 'dataset__name',
        'dataset__publication_id', 'dataset__publication__id', 'dataset__publication__journal',
        'dataset__publication__firstauthor', 'dataset__publication__date_publication',
        'dataset__platform__name', 'dataset__platform__platform_master__type',
        'dataset__tissue__id', 'dataset__tissue__label',
    ],
    'scores_pp_table': [
        *score_cols_base, 'ancestry',
        'dataset__id', 'dataset__name',
        'dataset__platform__version', *dataset_publication, *tissue_cols_base,
    ],
    'metabolite': [
        'id', 'name', 'external_id', 'pathway_group_id', 'pathway_subgroup_id',
        'pathway_group__id', 'pathway_group__name', 'pathway_subgroup__id', 'pathway_subgroup__name',
    ],
}

defer_dict = {
    'scores_table_defer': ['method_name', 'method_params', 'variants_interactions', 'variants_genomebuild', 'species', 'license'],
    'scores_defer': [
        'species',
        'dataset__species',
        'dataset__files_ids', 'dataset__license', 'dataset__method_name',
        'dataset__phewas_count', 'dataset__study_url', 'dataset__training_window',
        'dataset__scores_count', 'dataset__omics_count', 'dataset__omics_type',
        'dataset__publication__curation_notes',
        'dataset__publication__curation_status',
        'dataset__publication__date_released',
        'dataset__publication__authors',
        'dataset__publication__publication_type',
    ],
    'publication_defer': ['curation_notes', 'curation_status'],
}

performance_metric = [Prefetch('performance_metric', queryset=Metric.objects.only('id', 'performance_id', 'name_short', 'estimate').all())]
related_dict = {
    'metabolites': [Prefetch('metabolites', queryset=Metabolite.objects.only(*only_dict['metabolite']).select_related('pathway_group', 'pathway_subgroup').all().order_by('id'))],
    'proteins': [Prefetch('proteins', queryset=Protein.objects.only('id', 'name', 'external_id', 'external_id_source', 'description', 'synonyms').all().order_by('id'))],
    'genes': [Prefetch('genes', queryset=Gene.objects.only('id', 'name', 'external_id', 'external_id_source', 'synonyms', 'biotype', 'description', 'retired_gene_model').all().order_by('id'))],
    'molecular_traits': [
        Prefetch('genes', queryset=Gene.objects.defer('xrefs').all()),
        Prefetch('transcripts', queryset=Transcript.objects.defer('xrefs', 'gene_id').all()),
        Prefetch('proteins', queryset=Protein.objects.defer('xrefs', 'gene_id').all()),
        Prefetch('metabolites', queryset=Metabolite.objects.defer('description', 'pathway_group_id', 'pathway_subgroup_id').all()),
    ],
    'pathways': ['pathways', Prefetch('pathways__superpathways', queryset=SuperPathway.objects.only('id', 'name', 'external_id', 'external_id_source').all())],
    'pathway_prefetch_with_genes': [
        Prefetch('superpathways', queryset=SuperPathway.objects.only('id', 'name', 'external_id', 'external_id_source').all()),
        Prefetch('pathway_genes', queryset=Gene.objects.only('id', 'name', 'external_id', 'description').all()),
        Prefetch('pathway_genes__gene_score', queryset=Score.objects.only('num').all()),
    ],
    'pathway_prefetch_with_proteinss': [
        Prefetch('superpathways', queryset=SuperPathway.objects.only('id', 'name', 'external_id', 'external_id_source').all()),
        Prefetch('pathway_proteins', queryset=Protein.objects.only('id', 'name', 'external_id', 'description').all()),
        Prefetch('pathway_proteins__protein_score', queryset=Score.objects.only('num').all()),
    ],
    'pathway_prefetch_with_counts': [
        Prefetch('superpathways', queryset=SuperPathway.objects.only('id', 'name', 'external_id', 'external_id_source').all()),
        Prefetch('pathway_genes', queryset=Gene.objects.only('id').all()),
        Prefetch('pathway_proteins', queryset=Protein.objects.only('id').all()),
        Prefetch('pathway_metabolites', queryset=Metabolite.objects.only('id').all()),
    ],
    'performances': [Prefetch('score_performance', queryset=Performance.objects.defer('publication').select_related('sample').all().prefetch_related('sample__cohorts', 'performance_metric').order_by('id'))],
    'performance_cohorts': [Prefetch('score_performance', queryset=Performance.objects.only('id', 'score_id', 'cohort_label', 'eval_type').all().prefetch_related(*performance_metric).order_by('id'))],
    'perf_select': ['score', 'sample', 'dataset', 'dataset__publication', 'dataset__platform', 'dataset__platform__platform_master', 'dataset__tissue'],
    'dataset_select': ['platform', 'platform__platform_master', 'publication', 'tissue'],
    'dataset_prefetch': ['samples_training', 'samples_training__cohorts', 'samples_validation', 'samples_validation__cohorts'],
    'platform_prefetch': ['platform_version', 'platform_version__platform_dataset'],
    'publication_datasets': Prefetch('datasets', queryset=Dataset.objects.select_related('platform', 'platform__platform_master', 'tissue').all().prefetch_related('samples_training', 'samples_training__cohorts', 'samples_validation', 'samples_validation__cohorts').order_by('num')),
    'score_dataset': ['dataset', 'dataset__tissue', 'dataset__publication', 'dataset__platform'],
    'score_dataset_full': [
        'dataset',
        'dataset__tissue',
        'dataset__publication',
        'dataset__platform',
        'dataset__platform__platform_master',
    ],
    'score_search_cohort_training_via_dataset': [
        Prefetch('dataset__samples_training', queryset=Sample.objects.only('id', 'cohorts').all()),
    ],
    'score_search_cohort_validation_via_dataset': [
        Prefetch('dataset__samples_validation', queryset=Sample.objects.only('id', 'cohorts').all()),
    ],
    'score_phewas_select': [
        'score', 'publication',
        'score__dataset', 'score__dataset__publication', 'score__dataset__tissue',
        'score__dataset__platform', 'score__dataset__platform__platform_master',
    ],
    'score_phewas': [
        'score__genes', 'score__proteins', 'score__metabolites', 'score__transcripts',
        'phenotypes', 'samples', 'samples__cohorts',
    ],
    'tissue_prefetch': [Prefetch('tissue_dataset', queryset=Dataset.objects.only('id', 'tissue_id', 'scores_count').all())],
}
missing_index = 0


def get_score_queryset_base():
    return Score.objects.only(*only_dict['score']).select_related(*related_dict['score_dataset_full']).all().order_by('num')


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, Throttled):
        response.data = {'message': 'request limit exceeded', 'availableIn': f'{exc.wait} seconds'}
    elif isinstance(exc, ValidationError):
        formatted_exc = ''
        for key in exc.detail.keys():
            if formatted_exc:
                formatted_exc += '; '
            formatted_exc += str(exc.detail[key])
        response.data = {'status_code': response.status_code, 'message': formatted_exc}
    elif response is not None and response.status_code == status.HTTP_404_NOT_FOUND:
        response.data = {'status_code': status.HTTP_404_NOT_FOUND, 'message': 'This REST endpoint does not exist'}
    elif response is not None:
        response.data = {'status_code': response.status_code, 'message': str(exc)}
    else:
        response = Response({'status_code': status.HTTP_400_BAD_REQUEST, 'message': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return response


def warmup(request):
    import importlib
    for app in settings.INSTALLED_APPS:
        for name in ('urls', 'views', 'models'):
            try:
                importlib.import_module(f'{app}.{name}')
            except ImportError:
                pass
    return HttpResponse('Warmup done.', content_type='text/plain; charset=utf-8')
