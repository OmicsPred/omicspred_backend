from rest_framework import serializers
from omicspred.models import *
from applications.models import *
from plot.models import *


#### Cohort ####
class CohortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Cohort
        # meta_fields = ('name_short', 'name_full', 'name_others', 'url')
        meta_fields = ('name_short', 'name_full', 'description', 'url')
        fields = meta_fields
        read_only_fields = meta_fields


class CohortSerializerExtended(CohortSerializer):
    ancestries = serializers.SerializerMethodField()

    class Meta(CohortSerializer.Meta):
        meta_fields = ('ancestries',)
        fields = CohortSerializer.Meta.fields + meta_fields
        read_only_fields = CohortSerializer.Meta.read_only_fields + meta_fields

    def get_ancestries(self, obj):
        return sorted({x.ancestry_broad for x in obj.cohorts_sample.all()})


#### Sample ####
class SampleSerializer(serializers.ModelSerializer):
    cohorts = CohortSerializer(many=True, read_only=True)

    class Meta:
        model = Sample
        meta_fields = ('sample_number', 'sample_age', 'sample_age_sd', 'sample_percent_male',
                    'ancestry_broad', 'ancestry_free', 'ancestry_country', 'ancestry_additional',
                    'source_gwas_catalog', 'source_pmid','source_doi','cohorts','cohorts_additional')#,'tissue_name')
        fields = meta_fields
        read_only_fields = meta_fields


#### Tissue ####
class TissueSerializer(serializers.ModelSerializer):
    class Meta:
        model = EFO
        meta_fields = ('id', 'label', 'description', 'url', 'type')
        fields = meta_fields
        read_only_fields = meta_fields


class TissueSerializerScoresCount(TissueSerializer):
    class Meta(TissueSerializer.Meta):
        meta_fields = ('scores_count',)
        fields = TissueSerializer.Meta.fields + meta_fields
        read_only_fields = TissueSerializer.Meta.read_only_fields + meta_fields



#### Publication ####
class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publication
        meta_fields = ('id', 'title', 'doi', 'pmid', 'journal', 'firstauthor', 'date_publication')
        fields = meta_fields
        read_only_fields = meta_fields


#### Platform ####
class PlatformMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformMaster
        meta_fields = ('name', 'full_name', 'versions', 'technic', 'type', 'scores_count')
        fields = meta_fields
        read_only_fields = meta_fields


class PlatformSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField('get_full_name')
    technic = serializers.SerializerMethodField('get_technic')
    type = serializers.SerializerMethodField('get_type')

    class Meta:
        model = Platform
        meta_fields = ('name', 'full_name', 'version', 'technic', 'type')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_full_name(self, obj):
        full_name = obj.platform_master.full_name
        if full_name:
            return full_name
        else:
            return obj.name

    def get_technic(self, obj):
        return obj.platform_master.technic

    def get_type(self, obj):
        return obj.platform_master.type


class PlatformExtendedSerializer(PlatformSerializer):
    class Meta:
        model = Platform
        meta_fields = ('scores_count',)
        fields = PlatformSerializer.Meta.fields + meta_fields
        read_only_fields = PlatformSerializer.Meta.read_only_fields + meta_fields


#### Dataset ####
class DatasetLightSerializer(serializers.ModelSerializer):
    platform = PlatformSerializer(many=False, read_only=True)
    tissue = TissueSerializer(many=False, read_only=True)
    samples_training = SampleSerializer(many=True, read_only=True)
    samples_validation = SampleSerializer(many=True, read_only=True)

    class Meta:
        model = Dataset
        meta_fields = ('id', 'name', 'platform', 'scores_count', 'omics_count', 'omics_type',
                       'tissue', 'samples_training', 'samples_validation','scoring_files_urls')
        fields = meta_fields
        read_only_fields = meta_fields

class DatasetSerializer(DatasetLightSerializer):
    publication = PublicationSerializer(many=False, read_only=True)

    class Meta(DatasetLightSerializer.Meta):
        meta_fields = ('publication',)
        fields = DatasetLightSerializer.Meta.fields + meta_fields
        read_only_fields = DatasetLightSerializer.Meta.fields + meta_fields


#### Publication - Extended (with Platform) ####
class PublicationExtendedSerializer(PublicationSerializer):
    date_release = serializers.SerializerMethodField('get_date_released')
    datasets = DatasetLightSerializer(many=True, read_only=True)

    class Meta(PublicationSerializer.Meta):
        meta_fields = ('date_release', 'authors', 'datasets')
        fields = PublicationSerializer.Meta.fields + meta_fields
        read_only_fields = PublicationSerializer.Meta.read_only_fields + meta_fields

    def get_date_released(self, obj):
        return obj.date_released


#### Pathway ####
class PathwayOldSerializer(serializers.ModelSerializer):
    class Meta:
        model = PathwayOld
        meta_fields = ('name', 'external_id', 'external_id_source')
        fields = meta_fields
        read_only_fields = meta_fields


class SuperPathwaySerializer(serializers.ModelSerializer):
    class Meta:
        model = SuperPathway
        meta_fields = ('name', 'external_id', 'external_id_source')#, 'synonyms', 'xrefs')
        fields = meta_fields
        read_only_fields = meta_fields


class PathwaySerializer(serializers.ModelSerializer):
    superpathways = SuperPathwaySerializer(many=True, read_only=True)

    class Meta:
        model = Pathway
        meta_fields = ('name', 'external_id', 'external_id_source', 'synonyms', 'xrefs', 'superpathways')
        fields = meta_fields
        read_only_fields = meta_fields


#### Gene ####
class GeneSerializerMinimal(serializers.ModelSerializer):
    descriptions = serializers.SerializerMethodField()
    class Meta:
        model = Gene
        meta_fields = ('name','external_id','descriptions')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_descriptions(self, obj):
        if (obj.description):
            return obj.description_list
        return []


class GeneSerializer(GeneSerializerMinimal):
    synonyms = serializers.SerializerMethodField()
    # descriptions = serializers.SerializerMethodField()
    class Meta(GeneSerializerMinimal.Meta):
        meta_fields = ('external_id_source','synonyms', 'biotype')
        fields = GeneSerializerMinimal.Meta.fields + meta_fields
        read_only_fields = GeneSerializerMinimal.Meta.read_only_fields + meta_fields

    def get_synonyms(self, obj):
        if (obj.synonyms):
            return obj.synonyms_list
        return []


class GeneSerializerExtended(GeneSerializer):
    pathways = PathwaySerializer(many=True, read_only=True)

    class Meta(GeneSerializer.Meta):
        meta_fields = ('pathways',)
        fields = GeneSerializer.Meta.fields + meta_fields
        read_only_fields = GeneSerializer.Meta.read_only_fields + meta_fields


class GeneSerializerScoresCount(GeneSerializer):
    class Meta(GeneSerializer.Meta):
        meta_fields = ('scores_count',)
        fields = GeneSerializer.Meta.fields + meta_fields
        read_only_fields = GeneSerializer.Meta.read_only_fields + meta_fields


#### Transcript ####
class TranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcript
        meta_fields = ('name', 'external_id', 'external_id_source')
        fields = meta_fields
        read_only_fields = meta_fields


#### Protein ####
class ProteinSerializerMinimal(serializers.ModelSerializer):
    class Meta:
        model = Protein
        meta_fields = ('name','external_id')
        fields = meta_fields
        read_only_fields = meta_fields


class ProteinSerializer(ProteinSerializerMinimal):
    synonyms = serializers.SerializerMethodField()
    descriptions = serializers.SerializerMethodField()
    class Meta(ProteinSerializerMinimal.Meta):
        meta_fields = ('external_id_source','synonyms','descriptions')
        fields = ProteinSerializerMinimal.Meta.fields + meta_fields
        read_only_fields = ProteinSerializerMinimal.Meta.read_only_fields + meta_fields

    def get_synonyms(self, obj):
        if (obj.synonyms):
            return obj.synonyms_list
        return []

    def get_descriptions(self, obj):
        if (obj.description):
            return obj.description_list
        return []


class ProteinSerializerExtended(ProteinSerializer):
    gene = GeneSerializer(many=False, read_only=True)
    pathways = PathwaySerializer(many=True, read_only=True)
    # pathways = serializers.SerializerMethodField('get_pathways')

    class Meta(ProteinSerializer.Meta):
        meta_fields = ('gene','pathways')
        fields = ProteinSerializer.Meta.fields + meta_fields
        read_only_fields = ProteinSerializer.Meta.read_only_fields + meta_fields

    # def get_pathways(self, obj):
    #     pathways = []
    #     # Pathways
    #     if obj.gene:
    #         for pathway in obj.gene.pathways.prefetch_related('superpathways').all():
    #             pathway_entry = {}
    #             for field in PathwaySerializer.Meta.fields:
    #                 # Superpathways
    #                 if field == 'superpathways':
    #                     sp_pathways = []
    #                     superpathways = getattr(pathway, field)
    #                     for superpathway in superpathways.all():
    #                         sp_pathway_entry = {}
    #                         for sp_field in SuperPathwaySerializer.Meta.fields:
    #                             sp_pathway_entry[sp_field] = getattr(superpathway, sp_field)
    #                         sp_pathways.append(sp_pathway_entry)
    #                     pathway_entry[field] = sp_pathways
    #                 else:
    #                     pathway_entry[field] = getattr(pathway, field)
    #             pathways.append(pathway_entry)
    #     return pathways

class ProteinSerializerScoresCount(ProteinSerializer):
    class Meta(ProteinSerializer.Meta):
        meta_fields = ('scores_count',)
        fields = ProteinSerializer.Meta.fields + meta_fields
        read_only_fields = ProteinSerializer.Meta.read_only_fields + meta_fields


#### Metabolite ####
class MetaboliteLightSerializer(serializers.ModelSerializer):
    pathway_group = serializers.SerializerMethodField()
    pathway_subgroup = serializers.SerializerMethodField()
    class Meta:
        model = Metabolite
        meta_fields = ('name','external_id','pathway_group','pathway_subgroup')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_pathway_group(self, obj):
        if obj.pathway_group:
            return obj.pathway_group.name
        else:
            return None

    def get_pathway_subgroup(self, obj):
        if obj.pathway_subgroup:
            return obj.pathway_subgroup.name
        else:
            return None


class MetaboliteSerializerMinimal(serializers.ModelSerializer):

    class Meta:
        model = Metabolite
        meta_fields = ('name', 'external_id')
        fields = meta_fields
        read_only_fields = meta_fields


# /!\ Need to sort out the pathway_group/subgroup /!\
class MetaboliteSerializer(MetaboliteSerializerMinimal):
    synonyms = serializers.SerializerMethodField()
    # pathway_group = PathwaySerializer(many=False, read_only=True)
    # pathway_subgroup = PathwaySerializer(many=False, read_only=True)

    class Meta(MetaboliteSerializerMinimal.Meta):
        meta_fields = ('external_id_source', 'synonyms', 'xrefs') #,'pathway_group', 'pathway_subgroup')
        fields = MetaboliteSerializerMinimal.Meta.fields + meta_fields
        read_only_fields = MetaboliteSerializerMinimal.Meta.read_only_fields + meta_fields

    def get_synonyms(self, obj):
        if (obj.synonyms):
            return obj.synonyms_list
        return []


class MetaboliteSerializerExtended(MetaboliteSerializer):
    descriptions = serializers.SerializerMethodField()
    pathways = PathwaySerializer(many=True, read_only=True)

    class Meta(MetaboliteSerializer.Meta):
        meta_fields = ('descriptions', 'pathways',)
        fields = MetaboliteSerializer.Meta.fields + meta_fields
        read_only_fields = MetaboliteSerializer.Meta.read_only_fields + meta_fields

    def get_descriptions(self, obj):
        if (obj.description):
            return obj.description_list
        return []


class MetaboliteSerializerScoresCount(MetaboliteSerializer):
    class Meta(MetaboliteSerializer.Meta):
        meta_fields = ('scores_count',)
        fields = MetaboliteSerializer.Meta.fields + meta_fields
        read_only_fields = MetaboliteSerializer.Meta.read_only_fields + meta_fields


#### Pathway - Extended (with genes, proteins and metabolites) ####
class PathwaySerializerExtended(PathwaySerializer):
    # superpathways = SuperPathwaySerializer(many=True, read_only=True)
    genes = GeneSerializerScoresCount(source='pathway_genes', many=True, read_only=True)
    proteins = ProteinSerializerScoresCount(source='pathway_proteins', many=True, read_only=True)
    metabolites = MetaboliteSerializerScoresCount(source='pathway_metabolites', many=True, read_only=True)
    class Meta(PathwaySerializer.Meta):
        meta_fields = ('genes', 'proteins', 'metabolites')
        fields = PathwaySerializer.Meta.fields + meta_fields
        read_only_fields = PathwaySerializer.Meta.read_only_fields + meta_fields


# class PathwaySerializerExtended2(PathwaySerializer):
#     genes = GeneSerializerMinimal(source='pathway_genes', many=True, read_only=True)
#     proteins = ProteinSerializerMinimal(source='pathway_proteins', many=True, read_only=True)
#     metabolites = MetaboliteSerializerMinimal(source='pathway_metabolites', many=True, read_only=True)
#     class Meta(PathwaySerializer.Meta):
#         meta_fields = ('genes', 'proteins', 'metabolites')
#         fields = PathwaySerializer.Meta.fields + meta_fields
#         read_only_fields = PathwaySerializer.Meta.read_only_fields + meta_fields


class PathwaySerializerExtendedCount(PathwaySerializer):
    genes_count = serializers.SerializerMethodField()
    proteins_count = serializers.SerializerMethodField()
    metabolites_count = serializers.SerializerMethodField()
    class Meta(PathwaySerializer.Meta):
        meta_fields = ('genes_count', 'proteins_count', 'metabolites_count')
        fields = PathwaySerializer.Meta.fields + meta_fields
        read_only_fields = PathwaySerializer.Meta.read_only_fields + meta_fields

    def get_genes_count(self, obj):
        return obj.pathway_genes.count()

    def get_proteins_count(self, obj):
        return obj.pathway_proteins.count()

    def get_metabolites_count(self, obj):
        return obj.pathway_metabolites.count()


#### Score ####
class ScoreLightSerializer(serializers.ModelSerializer):
    dataset_id = serializers.SerializerMethodField()
    dataset_name = serializers.SerializerMethodField()
    publication = serializers.SerializerMethodField()
    platform = serializers.SerializerMethodField()
    tissue = serializers.SerializerMethodField()

    genes = GeneSerializer(many=True, read_only=True)
    transcripts = TranscriptSerializer(many=True, read_only=True)
    proteins = ProteinSerializer(many=True, read_only=True)
    metabolites = MetaboliteSerializer(many=True, read_only=True)
    # efos = TissueSerializer(many=True, read_only=True)

    # date_release = serializers.SerializerMethodField('get_date_released')

    class Meta:
        model = Score
        meta_fields = ('id', 'name', 'trait_reported', 'trait_reported_id', 'method_name', 'method_params',
                       'dataset_id', 'dataset_name', 'publication', 'platform', 'tissue', 'genes', 'transcripts', 'proteins', 'metabolites', #'efos',
                       'variants_number', 'variants_interactions', 'variants_genomebuild', 'comment', 'license')#, 'date_release')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_dataset_id(self,obj):
        ''' Get Dataset ID '''
        return obj.dataset.id

    def get_dataset_name(self,obj):
        ''' Get Dataset name '''
        return obj.dataset.name

    def get_publication(self, obj):
        ''' Get Publication model '''
        publication = obj.dataset.publication
        return PublicationSerializer(publication, many=False, read_only=True).data

    def get_platform(self, obj):
        ''' Get Platform model '''
        platform = obj.dataset.platform
        return PlatformSerializer(platform, many=False, read_only=True).data

    def get_tissue(self, obj):
        ''' Get Platform model '''
        tissue = obj.dataset.tissue
        return TissueSerializer(tissue, many=False, read_only=True).data


class ScoreSerializer(ScoreLightSerializer):
    class Meta(ScoreLightSerializer.Meta):
        meta_fields = ('ancestry',)
        fields = ScoreLightSerializer.Meta.fields + meta_fields
        read_only_fields = ScoreLightSerializer.Meta.read_only_fields + meta_fields


class ScorePathwaySerializer(ScoreSerializer):
    genes = GeneSerializerExtended(many=True, read_only=True)
    metabolites = MetaboliteSerializerExtended(many=True, read_only=True)

    class Meta(ScoreSerializer.Meta):
        fields = ScoreSerializer.Meta.fields
        read_only_fields = ScoreSerializer.Meta.read_only_fields


class GeneMinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gene
        meta_fields = ('name', 'external_id')
        fields = meta_fields
        read_only_fields = meta_fields

class TranscriptMinSerializer(serializers.ModelSerializer):
    class Meta:
        model =  Transcript
        meta_fields = ('name', 'external_id')
        fields = meta_fields
        read_only_fields = meta_fields

class ProteinMinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Protein
        meta_fields = ('name', 'external_id')
        fields = meta_fields
        read_only_fields = meta_fields

class MetaboliteMinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metabolite
        meta_fields = ('name', 'external_id')
        fields = meta_fields
        read_only_fields = meta_fields

class ScorePlotSerializer(serializers.ModelSerializer):
    genes = GeneMinSerializer(many=True, read_only=True)
    transcripts = TranscriptMinSerializer(many=True, read_only=True)
    proteins = ProteinMinSerializer(many=True, read_only=True)
    metabolites = MetaboliteMinSerializer(many=True, read_only=True)
    # genes = GeneSerializer(many=True, read_only=True)
    # transcripts = TranscriptSerializer(many=True, read_only=True)
    # proteins = ProteinSerializer(many=True, read_only=True)
    # metabolites = MetaboliteSerializer(many=True, read_only=True)

    class Meta:
        model = Score
        meta_fields = ('num', 'id', 'variants_number', 'genes', 'transcripts', 'proteins', 'metabolites')
        fields = meta_fields
        read_only_fields = meta_fields


#### Metric ####
class MetricSerializer(serializers.ModelSerializer):

    class Meta:
        model = Metric
        meta_fields = ('type', 'name', 'name_short', 'estimate', 'pvalue')
        fields = meta_fields
        read_only_fields = meta_fields


#### Performance ####
class PerformanceLightSerializer(serializers.ModelSerializer):
    evaluation_type = serializers.SerializerMethodField('get_eval_type_label')
    class Meta:
        model = Performance
        meta_fields = ('performance_metrics', 'cohort_label','performance_additional', 'evaluation_type', 'covariates')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_eval_type_label(self, obj):
        return obj.get_eval_type_display()


class PerformanceSerializer(serializers.ModelSerializer):
    publication = serializers.SerializerMethodField()
    platform = serializers.SerializerMethodField()
    tissue = serializers.SerializerMethodField()
    sample = SampleSerializer(many=False, read_only=True)

    evaluation_type = serializers.SerializerMethodField('get_eval_type_label')

    class Meta:
        model = Performance
        meta_fields = ('associated_opgs_id', 'publication', 'sample', 'platform', 'tissue',
                       'performance_metrics', 'cohort_label',
                       'evaluation_type', 'performance_additional', 'covariates')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_publication(self, obj):
        ''' Get Publication model '''
        publication = obj.dataset.publication
        return PublicationSerializer(publication, many=False, read_only=True).data

    def get_platform(self, obj):
        ''' Get Platform model '''
        platform = obj.dataset.platform
        return PlatformSerializer(platform, many=False, read_only=True).data

    def get_tissue(self, obj):
        ''' Get EFO/Tissue model '''
        tissue = obj.dataset.tissue
        return TissueSerializer(tissue, many=False, read_only=True).data

    def get_eval_type_label(self, obj):
        return obj.get_eval_type_display()


#### Score - Performance ####
class ScorePerformanceSerializer(ScoreSerializer):
    score_performance = PerformanceLightSerializer(many=True, read_only=True)

    class Meta(ScoreSerializer.Meta):
        meta_fields = ('score_performance',)
        fields = ScoreSerializer.Meta.fields + meta_fields
        read_only_fields = ScoreSerializer.Meta.read_only_fields + meta_fields


class ScorePerformanceDataSerializer(ScoreSerializer):
    class Meta(ScoreSerializer.Meta):
        meta_fields = ('performance_data',)
        fields = ScoreSerializer.Meta.fields + meta_fields
        read_only_fields = ScoreSerializer.Meta.read_only_fields + meta_fields



######## Omics tables ########

class ScoreMolecularTraitSerializer(serializers.ModelSerializer):
    dataset_id = serializers.SerializerMethodField()
    dataset_name = serializers.SerializerMethodField()
    publication = serializers.SerializerMethodField()
    platform_version = serializers.SerializerMethodField()

    class Meta:
        model = Score
        meta_fields = ('id','variants_number','dataset_id','dataset_name','platform_version','publication','ancestry')
        # meta_fields = ('id','variants_number','performance_range')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_dataset_id(self,obj):
        ''' Get Dataset ID '''
        return obj.dataset.id

    def get_dataset_name(self,obj):
        ''' Get Dataset name '''
        return obj.dataset.name

    def get_platform_version(self, obj):
        ''' Get Platform version '''
        return obj.dataset.platform.version

    def get_publication(self, obj):
        ''' Get Publication model '''
        publication = obj.dataset.publication
        return PublicationSerializer(publication, many=False, read_only=True).data


class ScoreMetaboliteSerializer(ScoreMolecularTraitSerializer):
    metabolites = MetaboliteLightSerializer(many=True, read_only=True)
    class Meta(ScoreMolecularTraitSerializer.Meta):
        meta_fields = ('trait_reported','trait_reported_id','metabolites')
        fields = ScoreMolecularTraitSerializer.Meta.fields + meta_fields
        read_only_fields = ScoreMolecularTraitSerializer.Meta.read_only_fields + meta_fields


class ScoreProteinSerializer(ScoreMolecularTraitSerializer):
    proteins = ProteinSerializer(many=True, read_only=True)
    genes = GeneSerializer(many=True, read_only=True)
    class Meta(ScoreMolecularTraitSerializer.Meta):
        meta_fields = ('genes','proteins')
        fields = ScoreMolecularTraitSerializer.Meta.fields + meta_fields
        read_only_fields = ScoreMolecularTraitSerializer.Meta.read_only_fields + meta_fields


class ScoreTranscriptSerializer(ScoreMolecularTraitSerializer):
    genes = GeneSerializer(many=True, read_only=True)
    class Meta(ScoreMolecularTraitSerializer.Meta):
        meta_fields = ('genes',)
        fields = ScoreMolecularTraitSerializer.Meta.fields + meta_fields
        read_only_fields = ScoreMolecularTraitSerializer.Meta.read_only_fields + meta_fields


# -- Omics with Performance data -- #

class ScorePerformanceMolecularTraitSerializer(ScoreMolecularTraitSerializer):
    class Meta(ScoreMolecularTraitSerializer.Meta):
        meta_fields = ('performance_data',)
        fields = ScoreMolecularTraitSerializer.Meta.fields + meta_fields
        read_only_fields = ScoreMolecularTraitSerializer.Meta.read_only_fields + meta_fields


class ScorePerformanceMetaboliteSerializer(ScorePerformanceMolecularTraitSerializer):
    metabolites = MetaboliteLightSerializer(many=True, read_only=True)
    class Meta(ScorePerformanceMolecularTraitSerializer.Meta):
        meta_fields = ('trait_reported','trait_reported_id','metabolites')
        fields = ScorePerformanceMolecularTraitSerializer.Meta.fields + meta_fields
        read_only_fields = ScorePerformanceMolecularTraitSerializer.Meta.read_only_fields + meta_fields


class ScorePerformanceProteinSerializer(ScorePerformanceMolecularTraitSerializer):
    proteins = ProteinSerializer(many=True, read_only=True)
    genes = GeneSerializer(many=True, read_only=True)
    class Meta(ScorePerformanceMolecularTraitSerializer.Meta):
        meta_fields = ('genes','proteins')
        fields = ScorePerformanceMolecularTraitSerializer.Meta.fields + meta_fields
        read_only_fields = ScorePerformanceMolecularTraitSerializer.Meta.read_only_fields + meta_fields


class ScorePerformanceTranscriptSerializer(ScorePerformanceMolecularTraitSerializer):
    genes = GeneSerializer(many=True, read_only=True)
    class Meta(ScorePerformanceMolecularTraitSerializer.Meta):
        meta_fields = ('genes',)
        fields = ScorePerformanceMolecularTraitSerializer.Meta.fields + meta_fields
        read_only_fields = ScorePerformanceMolecularTraitSerializer.Meta.read_only_fields + meta_fields


######################
#### Applications ####
######################

class PhenotypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phenotype
        meta_fields = ('id','name','category','source')
        fields = meta_fields
        read_only_fields = meta_fields


class PhenotypeSerializerScoresCount(PhenotypeSerializer):
    class Meta(PhenotypeSerializer.Meta):
        meta_fields = ('scores_count',)
        fields = PhenotypeSerializer.Meta.fields + meta_fields
        read_only_fields = PhenotypeSerializer.Meta.read_only_fields + meta_fields


class PhenotypeSerializerExtended(PhenotypeSerializerScoresCount):

    # child_phenotype = PhenotypeSerializer(many=True,read_only=True)
    child_phenotype = serializers.SerializerMethodField()

    class Meta(PhenotypeSerializerScoresCount.Meta):
        meta_fields = ('child_phenotype',)
        fields = PhenotypeSerializerScoresCount.Meta.fields + meta_fields
        read_only_fields = PhenotypeSerializerScoresCount.Meta.read_only_fields + meta_fields

    def get_child_phenotype(self, obj):
        ''' Sort phenotype child terms by their IDs '''
        children = obj.child_phenotype.prefetch_related('phenotype_score').order_by('id')
        return PhenotypeSerializerScoresCount(children, many=True).data


class PlatformApplicationsSerializer(PlatformSerializer):
    class Meta:
        model = PlatformApplications
        fields = PlatformSerializer.Meta.fields
        read_only_fields = PlatformSerializer.Meta.read_only_fields


class SampleApplicationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SampleApplications
        meta_fields = ('sample_number','sample_cases','sample_controls','sample_percent_female','sample_age', 'sample_age_sd')
        fields = meta_fields
        read_only_fields = meta_fields


class CohortApplicationsSerializer(CohortSerializer):
    class Meta:
        model = CohortApplications
        fields = CohortSerializer.Meta.fields
        read_only_fields = CohortSerializer.Meta.read_only_fields


class MolecularTraitApplicationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MolecularTraitApplications
        meta_fields = ('name','external_id','type')
        fields = meta_fields
        read_only_fields = meta_fields


class GeneApplicationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneApplications
        meta_fields = ('name','external_id')
        fields = meta_fields
        read_only_fields = meta_fields

class ProteinApplicationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProteinApplications
        meta_fields = ('name','external_id')
        fields = meta_fields
        read_only_fields = meta_fields

class MetaboliteApplicationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaboliteApplications
        meta_fields = ('name','external_id')
        fields = meta_fields
        read_only_fields = meta_fields


class ScoreApplicationsSerializer(serializers.ModelSerializer):
    phenotype = PhenotypeSerializer(many=False,read_only=True)
    platform = PlatformApplicationsSerializer(many=False,read_only=True)
    sample = SampleApplicationsSerializer(many=False,read_only=True)
    cohort = CohortApplicationsSerializer(many=False,read_only=True)
    genes = GeneApplicationsSerializer(many=True,read_only=True)
    proteins = ProteinApplicationsSerializer(many=True,read_only=True)
    metabolites = MetaboliteApplicationsSerializer(many=True,read_only=True)
    # molecular_traits = MolecularTraitApplicationsSerializer(many=True,read_only=True)
    data_values = serializers.SerializerMethodField('get_data_values')
    class Meta:
        model = ScoreApplications
        # meta_fields = ('score_id','phenotype','platform','sample','cohort','genes','proteins','metabolites','molecular_traits','data_values')
        meta_fields = ('score_id','phenotype','platform','sample','cohort','genes','proteins','metabolites','data_values')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_data_values(self, obj):
        return obj.values_dict


class SampleApplicationsLegacySerializer(serializers.ModelSerializer):
    phenotype = PhenotypeSerializerScoresCount(many=False,read_only=True)
    class Meta:
        model = SampleApplicationsLegacy
        meta_fields = ('sample_number','sample_cases','sample_percent_female','sample_age','sample_age_sd','phenotype','platform_counts')
        fields = meta_fields
        read_only_fields = meta_fields




###############
#### TESTS ####
###############

class PlotSerializer(serializers.ModelSerializer):

    class Meta:
        model = Plot
        meta_fields = ('dataset_id','dataset_name','plot_data','score_data')
        fields = meta_fields
        read_only_fields = meta_fields

# class ScoreExtendedSerializer(serializers.ModelSerializer):
#     publication = PublicationSerializer(many=False, read_only=True)
#     platform = PlatformSerializer(many=False, read_only=True)

#     genes = GeneSerializer(many=True, read_only=True)
#     transcripts = TranscriptSerializer(many=True, read_only=True)
#     proteins = ProteinSerializer(many=True, read_only=True)
#     metabolites = MetaboliteSerializer(many=True, read_only=True)
#     score_performance = PerformanceLightSerializer(many=True, read_only=True)

#     date_release = serializers.SerializerMethodField('get_date_released')

#     class Meta:
#         model = Score
#         meta_fields = ('id', 'name', 'trait_reported', 'trait_reported_id', 'method_name', 'method_params',
#                        'publication', 'platform', 'score_performance', 'genes', 'transcripts', 'proteins', 'metabolites', #'efos',
#                        'variants_number', 'variants_interactions', 'variants_genomebuild', 'date_release')
#         fields = meta_fields
#         read_only_fields = meta_fields

#     def get_date_released(self, obj):
#         return obj.date_released


# class OmicsScoreSerializer(serializers.ModelSerializer):
#     publication = PublicationSerializer(many=False, read_only=True)
#     platform = PlatformSerializer(many=False, read_only=True)

#     metabolites = MetaboliteSerializer(many=True, read_only=True)
#     score_performance = PerformanceLightSerializer(many=True, read_only=True)

#     class Meta:
#         model = Score
#         meta_fields = ('id', 'name', 'trait_reported', 'trait_reported_id', 'method_name', 'method_params',
#                     'publication', 'platform', 'score_performance',
#                     'variants_number', 'variants_interactions', 'variants_genomebuild')
#         fields = meta_fields
#         read_only_fields = meta_fields


# class MetaboliteScoreSerializer(OmicsScoreSerializer):
#     metabolites = MetaboliteSerializer(many=True, read_only=True)

#     class Meta(OmicsScoreSerializer):
#         meta_fields = ('metabolites',)
#         fields = OmicsScoreSerializer.Meta.fields + meta_fields
#         read_only_fields = OmicsScoreSerializer.Meta.read_only_fields + meta_fields


# class ProteinScoreSerializer(OmicsScoreSerializer):
#     genes = GeneSerializer(many=True, read_only=True)
#     proteins = ProteinSerializer(many=True, read_only=True)

#     class Meta(OmicsScoreSerializer):
#         meta_fields = ('genes', 'proteins')
#         fields = OmicsScoreSerializer.Meta.fields + meta_fields
#         read_only_fields = OmicsScoreSerializer.Meta.read_only_fields + meta_fields


# class TranscriptScoreSerializer(OmicsScoreSerializer):
#     genes = GeneSerializer(many=True, read_only=True)

#     class Meta(OmicsScoreSerializer):
#         meta_fields = ('genes',) # transcripts
#         fields = OmicsScoreSerializer.Meta.fields + meta_fields
#         read_only_fields = OmicsScoreSerializer.Meta.read_only_fields + meta_fields



# class OmicsPlotSerializer(serializers.ModelSerializer):
#     platform = PlatformSerializer(many=False, read_only=True)
#     sample = SampleSerializer(many=False, read_only=True)

#     class Meta:
#         model = Performance
#         meta_fields = ('score_id', 'platform', 'sample', 'performance_metrics')
#         fields = meta_fields
#         read_only_fields = meta_fields