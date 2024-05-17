from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from search_es.analyzers import id_analyzer, name_delimiter_analyzer
from omicspred.models import Score


# PGS index analyzer
id_analyzer = id_analyzer()
name_delimiter = name_delimiter_analyzer()


@registry.register_document
class ScoreDocument(Document):
    """ Score elasticsearch document """

    id = fields.TextField(analyzer=id_analyzer)
    name = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )
    # variants_number = fields.IntegerField()
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
    publication = fields.ObjectField(
        properties={
            'title': fields.TextField(),
            'pmid': fields.TextField(analyzer=id_analyzer),
            'doi': fields.TextField(analyzer=id_analyzer),
            'firstauthor': fields.KeywordField(),
        }
    )
    trait_reported = fields.TextField(
        fields={
            'raw': fields.KeywordField()
        }
    )
    trait_reported_id = fields.TextField(analyzer=id_analyzer)
    genes = fields.ObjectField(
        properties={
            'external_id': fields.TextField(),
            'name': fields.TextField(),
            'description': fields.TextField()
        }
    )
    proteins = fields.ObjectField(
        properties={
            'external_id': fields.TextField(),
            'name': fields.TextField(),
            'description': fields.TextField()
        }
    )
    metabolites = fields.ObjectField(
        properties={
            'external_id': fields.TextField(),
            'name': fields.TextField(),
            'description': fields.TextField()
        }
    )

    def prepare_platform_name(self, instance):
        return [instance.platform.name]

    def prepare_omics_type(self, instance):
        return [instance.platform.platform_master.type]


    class Index:
        name = settings.ELASTICSEARCH_INDEX_NAMES[__name__]
        settings = settings.ELASTICSEARCH_INDEX_SETTINGS

    class Django:
        """Inner nested class Django."""

        model = Score  # The model associated with this Document
        # Extra fields to store and return
        fields = [
            "variants_number"
        ]
        # fields = [
        #     "trait_reported",
        #     "trait_reported_id"
        # ]