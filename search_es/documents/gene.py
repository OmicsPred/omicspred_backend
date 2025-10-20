from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from search_es.analyzers import id_analyzer, name_delimiter_analyzer, word_delimiter_analyzer
from omicspred.models import Gene


# PGS index analyzer
id_analyzer = id_analyzer()
name_delimiter = name_delimiter_analyzer()
word_delimiter = word_delimiter_analyzer()


@registry.register_document
class GeneDocument(Document):
    """ Gene elasticsearch document """
    name = fields.TextField(
        analyzer=name_delimiter#,
        # fields={
        #     'raw': fields.KeywordField()
        # }
    )
    id = fields.TextField(attr="external_id", analyzer=id_analyzer)
    external_id_source = fields.TextField(index=False)
    synonyms_list = fields.TextField(
        analyzer=word_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )
    description = fields.TextField(
        analyzer=word_delimiter#,
        # fields={
        #     'raw': fields.KeywordField()
        # }
    )
    scores_count = fields.IntegerField(index=False, doc_values=False)
    platform_name = fields.TextField(index=False)
    omics_type = fields.TextField(index=False)
    biotype = fields.TextField(index=False)
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

    def prepare_platform_name(self, instance):
        platforms = set()
        for score in self.get_gene_scores(instance):
        # for score in instance.gene_score.all():
            platforms.add(score.dataset.platform.name)
        return list(platforms)

    def prepare_omics_type(self, instance):
        types = set()
        for score in self.get_gene_scores(instance):
        # for score in instance.gene_score.all():
            types.add(score.dataset.platform.platform_master.type)
        return list(types)

    def get_gene_scores(self, instance):
        return instance.gene_score.distinct('dataset__platform')


    class Index:
        name = settings.ELASTICSEARCH_INDEX_NAMES[__name__]
        settings = settings.ELASTICSEARCH_INDEX_SETTINGS


    class Django:
        """Inner nested class Django."""
        model = Gene # The model associated with this Document
        # queryset_pagination = settings.ELASTICSEARCH_DSL_QUERYSET_PAGINATION_SMALL # Index pagination
        # Extra fields to store and return
        # fields = [
        #     'biotype',
        #     'external_id_source'
        # ]
