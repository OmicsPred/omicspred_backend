from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from search_es.analyzers import id_analyzer, name_delimiter_analyzer, word_delimiter_analyzer
from omicspred.models import EFO


# PGS index analyzer
id_analyzer = id_analyzer()
name_delimiter = name_delimiter_analyzer()
word_delimiter = word_delimiter_analyzer()


@registry.register_document
class TissueDocument(Document):
    """ Tissue elasticsearch document """
    # 'label' preferred over 'name' to be more visible in the results
    label = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )
    id = fields.TextField(analyzer=id_analyzer)
    description = fields.TextField(
        analyzer=word_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )
    scores_count = fields.IntegerField()


    class Index:
        name = settings.ELASTICSEARCH_INDEX_NAMES[__name__]
        settings = settings.ELASTICSEARCH_INDEX_SETTINGS

    class Django:
        """Inner nested class Django."""

        model = EFO # The model associated with this Document
        # Extra fields to store and return
        # fields = []