from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from search.analyzers import name_delimiter_analyzer
from omicspred.models import Platform


# PGS index analyzer
name_delimiter = name_delimiter_analyzer()


@registry.register_document
class PlatformDocument(Document):
    """ Platform elasticsearch document """
    name = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )
    full_name = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )
    version = fields.TextField()
    technic = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )
    type = fields.TextField()
    scores_count = fields.IntegerField()

    def prepare_full_name(self, instance):
       return instance.platform_master.full_name

    def prepare_technic(self, instance):
       return instance.platform_master.technic

    def prepare_type(self, instance):
       return instance.platform_master.type


    class Index:
        name = settings.ELASTICSEARCH_INDEX_NAMES[__name__]
        settings = settings.ELASTICSEARCH_INDEX_SETTINGS

    class Django:
        """Inner nested class Django."""

        model = Platform # The model associated with this Document
        # Extra fields to store and return
        # fields = []