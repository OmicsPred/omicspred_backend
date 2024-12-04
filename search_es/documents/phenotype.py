from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from search_es.analyzers import id_analyzer, name_delimiter_analyzer
from applications.models import Phenotype


# PGS index analyzer
id_analyzer = id_analyzer()
name_delimiter = name_delimiter_analyzer()


@registry.register_document
class PhenotypeDocument(Document):
    """ Phenotype elasticsearch document """
    id = fields.TextField(analyzer=id_analyzer)
    name = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )
    category = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )
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
    phenotype_score = fields.ObjectField(
        properties={
            'score_id': fields.TextField()
        }
    )

    def prepare_platform_name(self, instance):
        return instance.platforms

    def prepare_omics_type(self, instance):
        return instance.omics_types


    class Index:
        name = settings.ELASTICSEARCH_INDEX_NAMES[__name__]
        settings = settings.ELASTICSEARCH_INDEX_SETTINGS

    class Django:
        """Inner nested class Django."""

        model = Phenotype # The model associated with this Document
        db = 'applications'
        # Extra fields to store and return
        fields = ['source']