from django.urls import path,re_path
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page
from .views import *


# Seconds * Minutes
#cache_time = 60 * 2
cache_time = 0

slash = '/?'

url_prefix = 'api'

rest_urls = {
    'cohort':               f'{url_prefix}/cohort/',
    'dataset':              f'{url_prefix}/dataset/',
    'external_source':      f'{url_prefix}/external_source/',
    'gene':                 f'{url_prefix}/gene/',
    'info':                 f'{url_prefix}/info',
    'metabolite':           f'{url_prefix}/metabolite/',
    'metabolomics':         f'{url_prefix}/metabolomics/',
    'pathway':              f'{url_prefix}/pathway/',
    'phenotype':            f'{url_prefix}/phenotype/',
    'phenotype_old':        f'{url_prefix}/phenotype_old/',
    'platform':             f'{url_prefix}/platform/',
    'plot':                 f'{url_prefix}/plot/',
    'performance':          f'{url_prefix}/performance/',
    'protein':              f'{url_prefix}/protein/',
    'proteomics':           f'{url_prefix}/proteomics/',
    'publication':          f'{url_prefix}/publication/',
    'sample':               f'{url_prefix}/sample/',
    'score':                f'{url_prefix}/score/',
    'tissue':               f'{url_prefix}/tissue/',
    'transcriptomics':      f'{url_prefix}/transcriptomics/'
}

urlpatterns = [
    # REST Documentation
    path('', TemplateView.as_view(template_name="rest_api/rest_doc.html")),
    # Cohorts
    re_path(r'^'+rest_urls['cohort']+'all'+slash, RestListCohorts.as_view(), name="getAllCohorts"),
    re_path(r'^'+rest_urls['cohort']+'(?P<cohort>[^/]+)'+slash, RestCohort.as_view(), name="getCohort"),
    # Pathways
    re_path(r'^'+rest_urls['pathway']+'all'+slash, RestListPathways.as_view(), name="getAllPathways"),
    re_path(r'^'+rest_urls['pathway']+'(?P<pathway_id>[^/]+)'+slash, RestPathway.as_view(), name="getPathway"),
    # Molecular trait
    re_path(r'^'+rest_urls['metabolite']+'search'+slash, RestSearchMetabolite.as_view(), name="searchMetabolites"),
    re_path(r'^'+rest_urls['metabolite']+'(?P<metabolite_id>[^/]+)'+slash, RestMetabolite.as_view(), name="getMetabolite"),
    re_path(r'^'+rest_urls['protein']+'search'+slash, RestSearchProtein.as_view(), name="searchProteins"),
    re_path(r'^'+rest_urls['protein']+'(?P<protein_id>[^/]+)'+slash, RestProtein.as_view(), name="getProtein"),
    re_path(r'^'+rest_urls['gene']+'search'+slash, RestSearchGene.as_view(), name="searchGenes"),
    re_path(r'^'+rest_urls['gene']+'(?P<gene_id>[^/]+)'+slash, RestGene.as_view(), name="getGene"),
    # Omics by platform
    re_path(r'^'+rest_urls['metabolomics']+'(?P<platform>[^/]+)'+slash, cache_page(cache_time)(RestMetabolomics.as_view()), name="getMetabolomicsScores"),
    re_path(r'^'+rest_urls['proteomics']+'(?P<platform>[^/]+)'+slash, cache_page(cache_time)(RestProteomics.as_view()), name="getProteomicsScores"),
    re_path(r'^'+rest_urls['transcriptomics']+'(?P<platform>[^/]+)'+slash, cache_page(cache_time)(RestTranscriptomics.as_view()), name="getTranscriptomicsScores"),
    # Performance metrics
    # re_path(r'^'+rest_urls['performance']+'all'+slash, cache_page(cache_time)(RestListPerformances.as_view()), name="getAllPerformanceMetrics"),
    re_path(r'^'+rest_urls['performance']+'search/(?P<type>[^/]+)/(?P<molecular_trait>[^/]+)'+slash, RestPerformanceSearchByMolecularTrait.as_view(), name="searchPerformancesByMolecularTrait"),
    re_path(r'^'+rest_urls['performance']+'search'+slash, RestPerformanceSearch.as_view(), name="searchPerformanceMetrics"),
    # Publication
    re_path(r'^'+rest_urls['publication']+'all'+slash, cache_page(cache_time)(RestListPublications.as_view()), name="getAllPublications"),
    re_path(r'^'+rest_urls['publication']+'search'+slash, cache_page(cache_time)(RestPublicationSearch.as_view()), name="searchPublications"),
    re_path(r'^'+rest_urls['publication']+'(?P<opp_id>[^/]+)'+slash, RestPublication.as_view(), name="getPublication"),
    # Samples
    re_path(r'^'+rest_urls['sample']+'all'+slash, cache_page(cache_time)(RestListSamples.as_view()), name="getAllSamples"),
    re_path(r'^'+rest_urls['sample']+'search'+slash, cache_page(cache_time)(RestSampleSearch.as_view()), name="searchSamples"),
    # Score PheWAS
    re_path(r'^'+rest_urls['score']+'phewas/all'+slash, cache_page(cache_time)(RestListScorePheWAS.as_view()), name="getAllScorePheWAS"),
    re_path(r'^'+rest_urls['score']+'phewas/search'+slash, RestScorePheWASSearch.as_view(), name="searchScorePheWAS"),
    re_path(r'^'+rest_urls['score']+'phewas/(?P<opgs_id>[^/]+)'+slash, cache_page(cache_time)(RestScorePheWAS.as_view()), name="getScorePheWAS"),
    # Scores
    re_path(r'^'+rest_urls['score']+'all'+slash, cache_page(cache_time)(RestListScores.as_view()), name="getAllScores"),
    re_path(r'^'+rest_urls['score']+'performance/(?P<opgs_id>[^/]+)'+slash, cache_page(cache_time)(RestScoreWithPerformance.as_view()), name="getScoreWithPerformance"),
    re_path(r'^'+rest_urls['score']+'search/(?P<type>[^/]+)/(?P<molecular_trait>[^/]+)'+slash, RestScoreSearchByMolecularTrait.as_view(), name="searchScoresByMolecularTrait"),
    re_path(r'^'+rest_urls['score']+'search'+slash, RestScoreSearch.as_view(), name="searchScores"),
    re_path(r'^'+rest_urls['score']+'(?P<opgs_id>[^/]+)'+slash, RestScore.as_view(), name="getScore"),
    # Dataset
    re_path(r'^'+rest_urls['dataset']+'all'+slash, cache_page(cache_time)(RestListDatasets.as_view()), name="getAllDatasets"),
    re_path(r'^'+rest_urls['dataset']+'search'+slash, cache_page(cache_time)(RestDatasetSearch.as_view()), name="searchDatasets"),
    re_path(r'^'+rest_urls['dataset']+'(?P<opd_id>[^/]+)'+slash, RestDataset.as_view(), name="getDataset"),
    # Platform
    re_path(r'^'+rest_urls['platform']+'all'+slash, cache_page(cache_time)(RestListPlatforms.as_view()), name="getAllPlatforms"),
    re_path(r'^'+rest_urls['platform']+'(?P<platform>[^/]+)'+slash, RestPlatform.as_view(), name="getPlatform"),
    # Tissue
    re_path(r'^'+rest_urls['tissue']+'all'+slash, cache_page(cache_time)(RestListTissues.as_view()), name="getAllTissues"),
    re_path(r'^'+rest_urls['tissue']+'(?P<tissue>[^/]+)'+slash, RestTissue.as_view(), name="getTissue"),
    # Phenotype
    re_path(r'^'+rest_urls['phenotype']+'all'+slash, RestListPhenotypes.as_view(), name="getAllPhenotypes"),
    re_path(r'^'+rest_urls['phenotype']+'(?P<phenotype_id>[^/]+)'+slash, RestPhenotype.as_view(), name="getPhenotype"),
    # Plot
    re_path(r'^'+rest_urls['plot']+'search'+slash, cache_page(cache_time)(RestPlotSearch.as_view()), name="searchPlots"),
    # To generate plot data
    re_path(r'^'+rest_urls['plot']+'file/search'+slash, cache_page(cache_time)(RestPlotFileSearch.as_view()), name="searchFilePlots"),
    re_path(r'^'+rest_urls['plot']+'score/search'+slash, cache_page(cache_time)(RestPlotScoreSearch.as_view()), name="searchScorePlots"),

    # Other
    re_path(r'^'+rest_urls['info']+slash, RestInfo.as_view(), name="getInfo"),
    # -> External sources
    re_path(r'^'+rest_urls['external_source']+'all'+slash, RestListExternalSources.as_view(), name="getAllExternalSources"),

    # Setup URL used to warmup the Django app in the Google App Engine
    path('_ah/warmup', warmup, name="Warmup"),
    # Robots file
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain"))
]

if settings.PUBLIC_SITE == False:
    # Plot
    urlpatterns.extend(
        [
            re_path(r'^'+rest_urls['plot']+'search'+slash, cache_page(cache_time)(RestPlotSearch.as_view()), name="searchPlots"),
            # To generate plot data
            re_path(r'^'+rest_urls['plot']+'file/search'+slash, cache_page(cache_time)(RestPlotFileSearch.as_view()), name="searchFilePlots"),
            re_path(r'^'+rest_urls['plot']+'score/search'+slash, cache_page(cache_time)(RestPlotScoreSearch.as_view()), name="searchScorePlots")
        ]
    )