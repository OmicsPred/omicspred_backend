from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from search_es.analyzers import id_analyzer, name_delimiter_analyzer, html_strip_analyzer
from omicspred.models import Protein


# PGS index analyzer
id_analyzer = id_analyzer()
html_strip = html_strip_analyzer()
name_delimiter = name_delimiter_analyzer()


@registry.register_document
class ProteinDocument(Document):
    """ Protein elasticsearch document """
    name = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )
    id = fields.TextField(attr="external_id", analyzer=id_analyzer)
    synonyms_list = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )
    description = fields.TextField(
        analyzer=html_strip,
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

    def prepare_platform_name(self, instance):
        platforms = set()
        for score in instance.protein_score.all():
            platforms.add(score.dataset.platform.name)
        return list(platforms)

    def prepare_omics_type(self, instance):
        types = set()
        for score in instance.protein_score.all():
            types.add(score.dataset.platform.platform_master.type)
        return list(types)


    class Index:
        name = settings.ELASTICSEARCH_INDEX_NAMES[__name__]
        settings = settings.ELASTICSEARCH_INDEX_SETTINGS

    class Django:
        """Inner nested class Django."""

        model = Protein # The model associated with this Document
        # Extra fields to store and return
        # fields = []