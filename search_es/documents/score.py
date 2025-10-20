from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from search_es.analyzers import id_analyzer, word_delimiter_analyzer, name_delimiter_analyzer
from omicspred.models import Score


# PGS index analyzer
id_analyzer = id_analyzer()
name_delimiter = name_delimiter_analyzer()
word_delimiter = word_delimiter_analyzer()


@registry.register_document
class ScoreDocument(Document):
    """ Score elasticsearch document """

    id = fields.TextField(analyzer=id_analyzer)
    name = fields.TextField(
        analyzer=name_delimiter#,
        # fields={
        #     'raw': fields.KeywordField()
        # }
    )
    variants_number = fields.IntegerField(index=False, doc_values=False)
    platform_name = fields.TextField(index=False)
    omics_type = fields.TextField(index=False)
    genes = fields.ObjectField(
        properties={
            'external_id': fields.TextField(index=False),
            'name': fields.TextField(index=False),
        }
    )
    proteins = fields.ObjectField(
        properties={
            'external_id': fields.TextField(index=False),
            'name': fields.TextField(index=False)
        }
    )
    metabolites = fields.ObjectField(
        properties={
            'external_id': fields.TextField(index=False),
            'name': fields.TextField(index=False)
        }
    )
    # platform_name = fields.TextField(
    #     analyzer=name_delimiter,
    #     fields={
    #         'raw': fields.KeywordField()
    #     }
    # )
    # omics_type = fields.TextField(
    #     analyzer=word_delimiter,
    #     fields={
    #         'raw': fields.KeywordField()
    #     }
    # )

    # >> Not searched and not displayed
    # publication = fields.ObjectField(
    #     properties={
    #         'title': fields.TextField(),
    #         'pmid': fields.TextField(analyzer=id_analyzer),
    #         'doi': fields.TextField(analyzer=id_analyzer),
    #         'firstauthor': fields.KeywordField(),
    #     }
    # )

    # trait_reported = fields.TextField(
    #     fields={
    #         'raw': fields.KeywordField()
    #     }
    # )
    # trait_reported_id = fields.TextField(analyzer=id_analyzer)
    # genes = fields.ObjectField(
    #     properties={
    #         'external_id': fields.TextField(
    #             analyzer=id_analyzer
    #         ),
    #         'name': fields.TextField(
    #             analyzer=word_delimiter,
    #             fields={
    #                 'raw': fields.KeywordField()
    #             }
    #         ),
    #         'description': fields.TextField(
    #             analyzer=word_delimiter#,
    #             # fields={
    #             #     'raw': fields.KeywordField()
    #             # }
    #         ),
    #         'synonyms_list': fields.TextField(
    #             analyzer=word_delimiter,
    #             fields={
    #                 'raw': fields.KeywordField()
    #             }
    #         )
    #     }
    # )
    # proteins = fields.ObjectField(
    #     properties={
    #        'external_id': fields.TextField(
    #             analyzer=id_analyzer
    #         ),
    #         'name': fields.TextField(
    #             analyzer=word_delimiter,
    #             fields={
    #                 'raw': fields.KeywordField()
    #             }
    #         ),
    #         'description': fields.TextField(
    #             analyzer=word_delimiter#,
    #             # fields={
    #             #     'raw': fields.KeywordField()
    #             # }
    #         ),
    #         'synonyms_list': fields.TextField(
    #             analyzer=word_delimiter,
    #             fields={
    #                 'raw': fields.KeywordField()
    #             }
    #         )
    #     }
    # )
    # metabolites = fields.ObjectField(
    #     properties={
    #         'external_id': fields.TextField(
    #             analyzer=id_analyzer
    #         ),
    #         'name': fields.TextField(
    #             analyzer=word_delimiter,
    #             fields={
    #                 'raw': fields.KeywordField()
    #             }
    #         ),
    #         'description': fields.TextField(
    #             analyzer=word_delimiter#,
    #             # fields={
    #             #     'raw': fields.KeywordField()
    #             # }
    #         ),
    #         'synonyms_list': fields.TextField(
    #             analyzer=word_delimiter,
    #             fields={
    #                 'raw': fields.KeywordField()
    #             }
    #         )
    #     }
    # )

    def prepare_platform_name(self, instance):
        return [instance.dataset.platform.name]

    def prepare_omics_type(self, instance):
        return [instance.dataset.platform.platform_master.type]


    class Index:
        name = settings.ELASTICSEARCH_INDEX_NAMES[__name__]
        settings = settings.ELASTICSEARCH_INDEX_SETTINGS

    class Django:
        """Inner nested class Django."""

        model = Score  # The model associated with this Document
        queryset_pagination = settings.ELASTICSEARCH_DSL_QUERYSET_PAGINATION # Index pagination
        # Extra fields to store and return
        # fields = [
        #     "variants_number"
        # ]