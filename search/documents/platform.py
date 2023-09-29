from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
from search.analyzers import name_delimiter_analyzer
from omicspred.models import Platform

# Name of the Elasticsearch index
INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES[__name__])

# See Elasticsearch Indices API reference for available settings
INDEX.settings(
    number_of_shards=1,
    number_of_replicas=1
)

# PGS index analyzer
name_delimiter = name_delimiter_analyzer()


@INDEX.doc_type
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


    class Django(object):
        """Inner nested class Django."""

        model = Platform # The model associated with this Document
