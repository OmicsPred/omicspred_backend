import operator
from functools import reduce

from django.db.models import Count, Q, QuerySet
from rest_framework.request import Request
from django.db.models.functions import Lower


OPGS_PREFIX = 'OPGS'
OPD_PREFIX = 'OPD'
OPP_PREFIX = 'OPP'
OPD_LENGTH = 9
OPP_LENGTH = 9


def normalize_query_param(request:Request, name: str) -> str:
    """Return a cleaned query param, stripping blank strings."""
    value = request.query_params.get(name)
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value if value else None
    return value


def get_num_from_id(entry_id: str, entry_prefix: str) -> int:
    entry_id = (entry_id or '').upper()
    entry_num = entry_id.replace(entry_prefix, '').lstrip('0')
    return int(entry_num) if entry_num else 0


def get_score_num(score_id: str) -> int:
    return get_num_from_id(score_id, OPGS_PREFIX)


def get_dataset_num(dataset_id: str) -> int:
    return get_num_from_id(dataset_id, OPD_PREFIX)


def get_publication_num(publication_id: str) -> int:
    return get_num_from_id(publication_id, OPP_PREFIX)


def get_ids_list(request) -> list[str]:
    """Extract IDs from either querystring or JSON payload."""
    ids = normalize_query_param(request,'filter_ids')
    if ids:
        return [x.upper() for x in ids.split(',') if x.strip()]

    data = getattr(request, 'data', {})
    if isinstance(data, dict) and 'filter_ids' in data:
        return [str(x).upper() for x in data['filter_ids'] if str(x).strip()]

    return []


def sort_data_list(request, type, queryset, default_col='num', distinct_col=None):
    if distinct_col is None:
        distinct_col = []
    request_url = request.get_full_path()
    sort_field = normalize_query_param(request, 'sort_field')
    if sort_field:
        if sort_field == f'{type}_id':
            sort_field = 'id'
        elif sort_field == f'{type}_name':
            sort_field = 'name'
        elif sort_field.endswith(f'_name') and not sort_field.endswith(f'__name'):
            sort_field = sort_field.replace('_name', '__name')
        queryset = queryset.distinct()
    elif distinct_col:
        queryset = queryset.distinct(*distinct_col)

    sort = normalize_query_param(request, 'sort')
    if not sort_field or sort_field is None:
        sort_field = default_col

    is_desc = sort == 'desc'
    if sort_field in ['genes_count', 'proteins_count', 'metabolites_count'] and type == 'pathway':
        mt_type = sort_field.split('_')[0]
        ordering = 'mt_count'
        if is_desc:
            ordering = '-mt_count'
        queryset = queryset.annotate(mt_count=Count('pathway_' + mt_type)).order_by(ordering)
    elif sort_field.endswith('name') and not request_url.startswith('/api/score/all'):
        if is_desc:
            queryset = queryset.order_by(Lower(sort_field).desc(nulls_last=True))
        else:
            queryset = queryset.order_by(Lower(sort_field).asc(nulls_last=True))
    else:
        if is_desc:
            sort_field = '-' + sort_field
        queryset = queryset.order_by(sort_field)
    return queryset


def filter_data(queryset, filter_params, data_type:str='score') -> QuerySet:
    """Parse a semicolon-delimited filter string used by some tables."""
    if filter_params and filter_params is not None:
        filter_params = filter_params.strip()
    else:
        return queryset

    query_prefix = ''
    if data_type == 'score':
        query_prefix = 'dataset__'

    filters_data = {}
    for chunk in filter_params.split(';'):
        if not chunk or ':' not in chunk:
            continue
        key, value = chunk.split(':', 1)
        filters_data[key] = value

    if not filters_data:
        return queryset

    query_filter_list = []
    dtype = {
        'Gene': 'genes',
        'Protein': 'proteins',
        'Metabolite': 'metabolites',
    }

    if 'anc' and 'stage' in filters_data:
        query_filter_list = filter_by_ancestry(filters_data)

    if 'score_id' in filters_data:
        filter_score_id = filters_data['score_id']
        if filter_score_id.startswith('OPGS'):
            score_num = get_score_num(filter_score_id)
            query_filter_list.append(Q(num=score_num))
        else:
            query_filter_list.append(Q(name__iexact=filter_score_id))

    if 'mt_id' in filters_data:
        mt_id = filters_data['mt_id']
        mt_type = filters_data['mt_type']
        if mt_type in dtype:
            mt_dtype_model = dtype[mt_type]
            query_filter_list.append(
                Q(**{f'{mt_dtype_model}__external_id__iexact': mt_id})
                | Q(**{f'{mt_dtype_model}__name__icontains': mt_id})
            )

    if 'platform' in filters_data:
        query_filter_list.append(Q(**{f'{query_prefix}platform__name__exact': filters_data['platform']}))

    if 'omics_type' in filters_data:
        query_filter_list.append(Q(**{f'{query_prefix}platform__platform_master__type__exact': filters_data['omics_type']}))

    if 'publication' in filters_data:
        pub_num = get_publication_num(filters_data['publication'])
        query_filter_list.append(Q(**{f'{query_prefix}publication_id': pub_num}))

    if 'tissue' in filters_data:
        query_filter_list.append(Q(**{f'{query_prefix}tissue__id__iexact': filters_data['tissue']}))

    if 'dataset' in filters_data:
        dataset_num = get_dataset_num(filters_data['dataset'])
        query_filter_list.append(Q(dataset__num=dataset_num))

    if 'gwas' in filters_data:
        query_filter_list.append(Q(samples__source_gwas_catalog__iexact=filters_data['gwas']))

    if not query_filter_list:
        return queryset

    return queryset.filter(reduce(operator.and_, query_filter_list))


def filter_by_ancestry(filters_data:dict) -> QuerySet:
    """Apply ancestry filters for training/validation/both stages."""
    ancestry = filters_data['anc']
    if not ancestry:
        return []

    anc_training_filter = Q(**{f'ancestry__dev__anc__{ancestry}__isnull': False})
    anc_validation_filter = Q(**{f'ancestry__eval__anc__{ancestry}__isnull': False})

    stage = filters_data['stage']
    match stage:
        case 't':
            return [anc_training_filter]
        case 'v':
            return [anc_validation_filter]
        case 'b':
            return [anc_training_filter & anc_validation_filter]
        case _:
            return [anc_training_filter | anc_validation_filter]


def filter_by_score(request:Request, queryset:QuerySet, params_count:int=None) -> QuerySet|tuple[int, QuerySet]:
    opgs_id = normalize_query_param(request,'opgs_id')
    if opgs_id and opgs_id is not None:
        if opgs_id.upper().startswith(OPGS_PREFIX):
            score_num = get_score_num(opgs_id)
            queryset = queryset.filter(score_id=score_num)
            if params_count is not None:
                params_count += 1
    if params_count is not None:
        return (params_count, queryset)
    return queryset
    

def filter_by_dataset(request:Request, queryset:QuerySet, params_count:int=None) -> QuerySet|tuple[int, QuerySet]:
    dataset = normalize_query_param(request,'dataset')
    if not dataset or dataset is None:
        dataset = normalize_query_param(request,'opd_id')
    if dataset and dataset is not None:
        if dataset.upper().startswith(OPD_PREFIX):
            dataset_num = get_dataset_num(dataset)
            queryset = queryset.filter(dataset__num=dataset_num)
            if params_count is not None:
                params_count += 1
    if params_count is not None:
        return (params_count, queryset)
    return queryset


def filter_by_platform(request:Request, queryset:QuerySet, params_count:int=None) -> QuerySet|tuple[int, QuerySet]:
    platform = normalize_query_param(request,'platform')
    if platform and platform is not None:
        queryset = queryset.filter(dataset__platform__name__iexact=platform)
        if params_count is not None:
            params_count += 1
    if params_count is not None:
        return (params_count, queryset)
    return queryset


def filter_by_publication(request:Request, queryset:QuerySet, params_count:int=None) -> QuerySet|tuple[bool, QuerySet]:
    opp_id = normalize_query_param(request,'opp_id')
    if opp_id and opp_id is not None:
        if opp_id.upper().startswith(OPP_PREFIX):
            publication_num = get_publication_num(opp_id)
            queryset = queryset.filter(Q(dataset__publication__num=publication_num))
            if params_count is not None:
                params_count += 1
    if params_count is not None:
        return (params_count, queryset)
    return queryset
            

def filter_by_pmid(request:Request, queryset:QuerySet, params_count:int=None) -> QuerySet|tuple[int, QuerySet]:
    pmid = normalize_query_param(request,'pmid')
    if pmid and pmid is not None:
        queryset = queryset.filter(Q(dataset__publication__pmid=pmid) | Q(dataset__publication__doi__iexact=pmid))
        if params_count is not None:
            params_count += 1
    if params_count is not None:
        return (params_count, queryset)
    return queryset


def filter_by_pathway(request:Request, queryset:QuerySet, params_count:int=None) -> QuerySet|tuple[int, QuerySet]:
    pathway = normalize_query_param(request,'pathway')
    if pathway and pathway is not None:
        queryset = queryset.filter(pathways__external_id=pathway)
        if params_count is not None:
            params_count += 1
    if params_count is not None:
        return (params_count, queryset)
    return queryset


def filter_by_platform_version(request:Request, queryset:QuerySet, params_count:int=None) -> QuerySet|tuple[int, QuerySet]:
    version = normalize_query_param(request,'version')
    if version and version is not None:
        queryset = queryset.filter(dataset__platform__version=version)
        if params_count is not None:
            params_count += 1
    if params_count is not None:
        return (params_count, queryset)
    return queryset