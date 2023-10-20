from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
from search.analyzers import id_analyzer, name_delimiter_analyzer
from omicspred.models import Metabolite

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


@INDEX.doc_type
class MetaboliteDocument(Document):
    """ Metabolite elasticsearch document """
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
        for score in instance.metabolite_score.all():
            platforms.add(score.platform.name)
        return list(platforms)

    def prepare_omics_type(self, instance):
        types = set()
        for score in instance.metabolite_score.all():
            types.add(score.platform.type)
        return list(types)


    class Django(object):
        """Inner nested class Django."""

        model = Metabolite # The model associated with this Document
