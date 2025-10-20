from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from search_es.analyzers import id_analyzer, name_delimiter_analyzer, word_delimiter_analyzer
from applications.models import Phenotype


# PGS index analyzer
id_analyzer = id_analyzer()
name_delimiter = name_delimiter_analyzer()
word_delimiter = word_delimiter_analyzer()


@registry.register_document
class PhenotypeDocument(Document):
    """ Phenotype elasticsearch document """
    id = fields.TextField(analyzer=id_analyzer)
    name = fields.TextField(
        analyzer=name_delimiter#,
        # fields={
        #     'raw': fields.KeywordField()
        # }
    )
    category = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )
    scores_count = fields.IntegerField(index=False)
    platform_name = fields.TextField(index=False)
    omics_type = fields.TextField(index=False)
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
    phenotype_score = fields.ObjectField(
        properties={
            'score_id': fields.TextField(analyzer=id_analyzer)
        }
    )
    # molecular_traits = fields.ObjectField(
    #     properties={
    #         'external_id': fields.TextField(),
    #         'name': fields.TextField()
    #     }
    # )

    def prepare_platform_name(self, instance):
        return instance.platforms

    def prepare_omics_type(self, instance):
        return instance.omics_types

    # def prepare_molecular_traits(self, instance):
    #     scores = instance.phenotype_score.all()
    #     molecular_trait_ids = []
    #     molecular_traits = []
    #     for score in scores:
    #         for molecular_trait in score.molecular_traits.all():
    #             id = molecular_trait.external_id
    #             name = molecular_trait.name
    #             type = molecular_trait.type
    #             internal_id = id if id else name
    #             internal_id += '_'+type
    #             if not internal_id in molecular_trait_ids:
    #                 molecular_trait_dict = {
    #                     'external_id': molecular_trait.external_id,
    #                     'name': molecular_trait.name
    #                 }
    #                 molecular_traits.append(molecular_trait_dict)
    #                 molecular_trait_ids.append(internal_id)
    #     return molecular_traits


    class Index:
        name = settings.ELASTICSEARCH_INDEX_NAMES[__name__]
        settings = settings.ELASTICSEARCH_INDEX_SETTINGS

    class Django:
        """Inner nested class Django."""

        model = Phenotype # The model associated with this Document
        # queryset_pagination = settings.ELASTICSEARCH_DSL_QUERYSET_PAGINATION_SMALL # Index pagination
        db = 'applications'
        # Extra fields to store and return
        fields = ['source']