from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from search_es.analyzers import id_analyzer, name_delimiter_analyzer, word_delimiter_analyzer
from omicspred.models import Pathway


# PGS index analyzer
id_analyzer = id_analyzer()
name_delimiter = name_delimiter_analyzer()
word_delimiter = word_delimiter_analyzer()

mt_attr_list = ['external_id','name','description','synonyms_list']
mt_fields_list = ['external_id','name','description','synonyms']

def fetch_mt_data(objects_list):
    mt_list = []
    for mt in objects_list:
        mt_entry = {}
        for entity in mt_attr_list:
            mt_entry[entity] = getattr(mt, entity)
        mt_list.append(mt_entry)
    return mt_list


@registry.register_document
class PathwayDocument(Document):
    """ Pathway elasticsearch document """
    name = fields.TextField(
        analyzer=name_delimiter#,
        # fields={
        #     'raw': fields.KeywordField()
        # }
    )
    id = fields.TextField(attr="external_id", analyzer=id_analyzer)
    external_id_source = fields.TextField(index=False)
    synonyms_list = fields.TextField(
        analyzer=word_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )
    description = fields.TextField(
        analyzer=word_delimiter#,
        # fields={
        #     'raw': fields.KeywordField()
        # }
    )
    genes = fields.ObjectField(
        properties={
            'external_id': fields.TextField(
                analyzer=id_analyzer
            ),
            'name': fields.TextField(
                analyzer=word_delimiter,
                fields={
                    'raw': fields.KeywordField()
                }
            ),
            'description': fields.TextField(
                analyzer=word_delimiter#,
                # fields={
                #     'raw': fields.KeywordField()
                # }
            ),
            'synonyms_list': fields.TextField(
                analyzer=word_delimiter,
                fields={
                    'raw': fields.KeywordField()
                }
            )
        }
    )
    proteins = fields.ObjectField(
        properties={
            'external_id': fields.TextField(
                analyzer=id_analyzer
            ),
            'name': fields.TextField(
                analyzer=word_delimiter,
                fields={
                    'raw': fields.KeywordField()
                }
            ),
            'description': fields.TextField(
                analyzer=word_delimiter#,
                # fields={
                #     'raw': fields.KeywordField()
                # }
            ),
            'synonyms_list': fields.TextField(
                analyzer=word_delimiter,
                fields={
                    'raw': fields.KeywordField()
                }
            )
        }
    )
    metabolites = fields.ObjectField(
        properties={
            'external_id': fields.TextField(
                analyzer=id_analyzer
            ),
            'name': fields.TextField(
                analyzer=word_delimiter,
                fields={
                    'raw': fields.KeywordField()
                }
            ),
            'description': fields.TextField(
                analyzer=word_delimiter#,
                # fields={
                #     'raw': fields.KeywordField()
                # }
            ),
            'synonyms_list': fields.TextField(
                analyzer=word_delimiter,
                fields={
                    'raw': fields.KeywordField()
                }
            )
        }
    )
    
    def prepare_genes(self, instance):
        genes = instance.pathway_genes.only(*mt_fields_list).all().distinct()
        return fetch_mt_data(genes)
    
    def prepare_proteins(self, instance):
        proteins = instance.pathway_proteins.only(*mt_fields_list).all().distinct()
        return fetch_mt_data(proteins)

    def prepare_metabolites(self, instance):
        metabolites = instance.pathway_metabolites.only(*mt_fields_list).all().distinct()
        return fetch_mt_data(metabolites)


    class Index:
        name = settings.ELASTICSEARCH_INDEX_NAMES[__name__]
        settings = settings.ELASTICSEARCH_INDEX_SETTINGS


    class Django:
        """Inner nested class Django."""

        model = Pathway # The model associated with this Document
        # queryset_pagination = settings.ELASTICSEARCH_DSL_QUERYSET_PAGINATION_SMALL # Index pagination
        # Extra fields to store and return
        # fields = ['external_id_source']