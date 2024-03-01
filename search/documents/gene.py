from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from search.analyzers import id_analyzer, name_delimiter_analyzer
from omicspred.models import Gene


# PGS index analyzer
id_analyzer = id_analyzer()
name_delimiter = name_delimiter_analyzer()


@registry.register_document
class GeneDocument(Document):
    """ Gene elasticsearch document """
    name = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )
    id = fields.TextField(attr="external_id", analyzer=id_analyzer)
    # synonyms = fields.TextField(
    #     properties={
    #         'raw': fields.KeywordField()
    #     }
    # )
    scores_count = fields.IntegerField()
    platform_name = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )
    omics_type = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )

    def prepare_platform_name(self, instance):
        platforms = set()
        for score in instance.gene_score.all():
            platforms.add(score.platform.name)
        return list(platforms)

    def prepare_omics_type(self, instance):
        types = set()
        for score in instance.gene_score.all():
            types.add(score.platform.platform_master.type)
        return list(types)


    class Index:
        name = settings.ELASTICSEARCH_INDEX_NAMES[__name__]
        settings = settings.ELASTICSEARCH_INDEX_SETTINGS

    class Django:
        """Inner nested class Django."""
        model = Gene # The model associated with this Document
        # Extra fields to store and return
        fields = [
            "biotype"
        ]
