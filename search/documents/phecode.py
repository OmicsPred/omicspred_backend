from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
from search.analyzers import id_analyzer, name_delimiter_analyzer
from applications.models import Phecode

# Name of the Elasticsearch index
INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES[__name__])

# See Elasticsearch Indices API reference for available settings
INDEX.settings(
    number_of_shards=1,
    number_of_replicas=1
)

# PGS index analyzer
id_analyzer = id_analyzer()
name_delimiter = name_delimiter_analyzer()


@INDEX.document
class PhecodeDocument(Document):
    """ Phecode elasticsearch document """
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


    def prepare_platform_name(self, instance):
        return instance.platforms

    def prepare_omics_type(self, instance):
        return instance.omics_types


    class Django(object):
        """Inner nested class Django."""

        model = Phecode # The model associated with this Document
        db = 'applications'
