from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from search_es.analyzers import id_analyzer, word_delimiter_analyzer, name_delimiter_analyzer
from omicspred.models import Score, Dataset


# PGS index analyzer
id_analyzer = id_analyzer()
name_delimiter = name_delimiter_analyzer()
word_delimiter = word_delimiter_analyzer()

molecular_trait_attr = ['external_id','name']
omics_types_list = {
    "protein": "Proteomics",
    "metabolite": "Metabolomics",
    "gene expression": "Transcriptomics"
}


@registry.register_document
class ScoreDocument(Document):
    """ Score elasticsearch document """

    id = fields.TextField(analyzer=id_analyzer)
    name = fields.TextField(
        analyzer=name_delimiter#,
        # fields={
        #     'raw': fields.KeywordField()
        # }
    )
    variants_number = fields.IntegerField(index=False, doc_values=False)
    platform_name = fields.TextField(index=False)
    omics_type = fields.TextField(index=False)
    genes_data = fields.ObjectField(
        properties={
            'external_id': fields.TextField(index=False),
            'name': fields.TextField(index=False),
        }
    )
    proteins_data = fields.ObjectField(
        properties={
            'external_id': fields.TextField(index=False),
            'name': fields.TextField(index=False)
        }
    )
    metabolites_data = fields.ObjectField(
        properties={
            'external_id': fields.TextField(index=False),
            'name': fields.TextField(index=False)
        }
    )

    def prepare_genes_data(self, instance):
        # Limit fetch of gene data to protein and gene platforms
        omics_type = self.get_omics_type(instance)
        if omics_type in ['protein', 'gene expression']:
            genes_db = instance.genes.only(*molecular_trait_attr).all().distinct('id')
            return self.get_molecular_traits(genes_db)
        else:
            return []

    def prepare_proteins_data(self, instance):
        # Limit fetch of protein data to protein platforms
        omics_type = self.get_omics_type(instance)
        if omics_type in ['protein']:
            proteins_db = instance.proteins.only(*molecular_trait_attr).all().distinct('id')
            return self.get_molecular_traits(proteins_db)
        else:
            return []

    def prepare_metabolites_data(self, instance):
        # Limit fetch of metabolite data to metabolite platforms
        omics_type = self.get_omics_type(instance)
        if omics_type in ['metabolite']:
            metabolites_db = instance.metabolites.only(*molecular_trait_attr).all().distinct('id')
            return self.get_molecular_traits(metabolites_db)
        else:
            return []

    def prepare_platform_name(self, instance):
        dataset_id = instance.dataset_id
        dataset = Dataset.objects.only('platform__name').get(num=dataset_id)
        # dataset = Dataset.objects.only('platform__name').select_related('platform').get(num=dataset_id)
        return [dataset.platform.name]
        # return [instance.dataset.platform.name]

    def prepare_omics_type(self, instance):
        omics_type = self.get_omics_type(instance)
        return [omics_types_list[omics_type]]

    def get_omics_type(self,instance):
        dataset_id = instance.dataset_id
        dataset = Dataset.objects.only('omics_type').get(num=dataset_id)
        return dataset.omics_type

    # def get_molecular_traits_data(self,mt_model):
    #     return {'external_id': mt_model.external_id,'name': mt_model.name}

    def get_molecular_traits(self,mt_db_list):
        # # Test with classic loop
        # mt_list = []
        # for mt_db in mt_db_list:
        #     mt_list.append({'external_id': mt_db.external_id,'name': mt_db.name})
        # return mt_list
        # # Test with map
        # mt_list = map(self.get_molecular_traits_data,mt_db_list)
        # return list(mt_list)
        # Test with List Comprehension
        return [ {'external_id': mt_db.external_id,'name': mt_db.name} for mt_db in mt_db_list ]


    class Index:
        name = settings.ELASTICSEARCH_INDEX_NAMES[__name__]
        settings = settings.ELASTICSEARCH_INDEX_SETTINGS

    class Django:
        """Inner nested class Django."""

        model = Score  # The model associated with this Document
        queryset_pagination = settings.ELASTICSEARCH_DSL_QUERYSET_PAGINATION # Index pagination
        # Extra fields to store and return
        # fields = [
        #     "variants_number"
        # ]