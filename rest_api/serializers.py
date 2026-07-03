from rest_framework import serializers
from omicspred.models import *
from applications.models import Phenotype as PhenotypeOld
from applications.models import ScoreApplications,SampleApplications,SampleApplicationsLegacy,PlatformApplications,CohortApplications,MolecularTraitApplications,GeneApplications,ProteinApplications,MetaboliteApplications
from plot.models import *


# Global variables
scores_count = ('scores_count',)


###################
#### OmicsPred ####
###################

#### External Source ####
class ExternalSourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExternalSource
        meta_fields = ('name', 'version', 'url')
        fields = meta_fields
        read_only_fields = meta_fields


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
    ancestry_assignment = serializers.SerializerMethodField('get_ancestry_assignment_label')

    class Meta:
        model = Sample
        meta_fields = ('sample_number', 'sample_cases', 'sample_controls',
                       'sample_age', 'sample_age_sd', 'sample_percent_male',
                       'ancestry_broad', 'ancestry_free', 'ancestry_country', 'ancestry_additional', 'ancestry_assignment',
                       'source_gwas_catalog', 'source_pmid','source_doi','cohorts','cohorts_additional')#,'tissue_name')
        fields = meta_fields
        read_only_fields = meta_fields
    
    def get_ancestry_assignment_label(self, obj):
        return obj.get_ancestry_assignment_display()


#### Tissue ####
class TissueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tissue
        meta_fields = ('id', 'label', 'description', 'url', 'type')
        fields = meta_fields
        read_only_fields = meta_fields


class TissueSerializerScoresCount(TissueSerializer):
    class Meta(TissueSerializer.Meta):
        meta_fields = scores_count
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
        meta_fields = ('name', 'full_name', 'versions', 'technique', 'type', 'scores_count')
        fields = meta_fields
        read_only_fields = meta_fields


class PlatformSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField('get_full_name')
    technique = serializers.SerializerMethodField('get_technique')
    type = serializers.SerializerMethodField('get_type')

    class Meta:
        model = Platform
        meta_fields = ('name', 'full_name', 'version', 'technique', 'type')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_full_name(self, obj):
        full_name = obj.platform_master.full_name
        if full_name:
            return full_name
        else:
            return obj.name

    def get_technique(self, obj):
        return obj.platform_master.technique

    def get_type(self, obj):
        return obj.platform_master.type


class PlatformExtendedSerializer(PlatformSerializer):
    class Meta:
        model = Platform
        meta_fields = scores_count
        fields = PlatformSerializer.Meta.fields + meta_fields
        read_only_fields = PlatformSerializer.Meta.read_only_fields + meta_fields


#### Dataset ####
class DatasetLightSerializer(serializers.ModelSerializer):
    platform = PlatformSerializer(many=False, read_only=True)
    tissue = TissueSerializer(many=False, read_only=True)
    samples_training = SampleSerializer(many=True, read_only=True)
    samples_validation = SampleSerializer(many=True, read_only=True)
    training_window = serializers.SerializerMethodField('get_training_window_label')

    class Meta:
        model = Dataset
        meta_fields = ('id', 'name', 'platform', 'scores_count', 'omics_count', 'phewas_count', 'omics_type', 'method_name',
                       'training_window', 'tissue', 'samples_training', 'samples_validation','scoring_files_urls')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_training_window_label(self, obj):
        return obj.get_training_window_display()


class DatasetSerializer(DatasetLightSerializer):
    publication = PublicationSerializer(many=False, read_only=True)

    class Meta(DatasetLightSerializer.Meta):
        meta_fields = ('publication','license')
        fields = DatasetLightSerializer.Meta.fields + meta_fields
        read_only_fields = DatasetLightSerializer.Meta.fields + meta_fields


class DatasetPheWASPublicationSerializer(DatasetSerializer):
    phewas_publications = PublicationSerializer(many=True, read_only=True)

    class Meta(DatasetSerializer.Meta):
        meta_fields = ('phewas_publications',)
        fields = DatasetSerializer.Meta.fields + meta_fields
        read_only_fields = DatasetSerializer.Meta.fields + meta_fields

    def get_phewas_publications(self, obj):
        if (obj.phewas_publications):
            return obj.phewas_publications
        return []


#### Publication - Extended (with Platform) ####
class PublicationExtendedSerializer(PublicationSerializer):
    date_release = serializers.SerializerMethodField('get_date_released')
    datasets = DatasetLightSerializer(many=True, read_only=True)

    class Meta(PublicationSerializer.Meta):
        meta_fields = ('publication_type', 'date_release', 'authors', 'datasets', 'phewas_count')
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
    parent_external_ids = serializers.SerializerMethodField()
    superpathways = SuperPathwaySerializer(many=True, read_only=True)

    class Meta:
        model = Pathway
        meta_fields = ('name', 'external_id', 'external_id_source', 'parent_external_ids', 'synonyms', 'xrefs', 'superpathways', 'top_level')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_parent_external_ids(self, obj):
        if (obj.parent_external_id):
            return obj.parent_external_ids_list
        return []


#### Gene ####
class GeneBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gene
        meta_fields = ('name', 'external_id')
        fields = meta_fields
        read_only_fields = meta_fields


class GeneSerializerMinimal(GeneBaseSerializer):
    descriptions = serializers.SerializerMethodField()

    class Meta(GeneBaseSerializer.Meta):
        model = Gene
        meta_fields = ('descriptions',)
        fields = GeneBaseSerializer.Meta.fields + meta_fields
        read_only_fields = GeneBaseSerializer.Meta.read_only_fields + meta_fields

    def get_descriptions(self, obj):
        if (obj.description):
            return obj.description_list
        return []


class GeneSerializer(GeneSerializerMinimal):
    synonyms = serializers.SerializerMethodField()

    class Meta(GeneSerializerMinimal.Meta):
        meta_fields = ('external_id_source','synonyms', 'biotype', 'retired_gene_model')
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


class GeneSerializerScoresCount(GeneSerializerMinimal):
    class Meta(GeneSerializerMinimal.Meta):
        meta_fields = scores_count
        fields = GeneSerializerMinimal.Meta.fields + meta_fields
        read_only_fields = GeneSerializerMinimal.Meta.read_only_fields + meta_fields


class GeneSerializerExtendedScoresCount(GeneSerializerExtended):
    class Meta(GeneSerializer.Meta):
        meta_fields = scores_count
        fields = GeneSerializerExtended.Meta.fields + meta_fields
        read_only_fields = GeneSerializerExtended.Meta.read_only_fields + meta_fields


#### Transcript ####
class TranscriptBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model =  Transcript
        meta_fields = ('name', 'external_id')
        fields = meta_fields
        read_only_fields = meta_fields


class TranscriptSerializer(TranscriptBaseSerializer):
    class Meta(TranscriptBaseSerializer.Meta):
        model = Transcript
        meta_fields = ('external_id_source',)
        fields =  TranscriptBaseSerializer.Meta.fields + meta_fields
        read_only_fields = TranscriptBaseSerializer.Meta.fields + meta_fields


#### Protein ####
class ProteinBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Protein
        meta_fields = ('name','external_id')
        fields = meta_fields
        read_only_fields = meta_fields


class ProteinSerializer(ProteinBaseSerializer):
    synonyms = serializers.SerializerMethodField()
    descriptions = serializers.SerializerMethodField()

    class Meta(ProteinBaseSerializer.Meta):
        meta_fields = ('external_id_source','synonyms','descriptions')
        fields = ProteinBaseSerializer.Meta.fields + meta_fields
        read_only_fields = ProteinBaseSerializer.Meta.read_only_fields + meta_fields

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

    class Meta(ProteinSerializer.Meta):
        meta_fields = ('gene','pathways')
        fields = ProteinSerializer.Meta.fields + meta_fields
        read_only_fields = ProteinSerializer.Meta.read_only_fields + meta_fields


class ProteinSerializerScoresCount(ProteinBaseSerializer):
    descriptions = serializers.SerializerMethodField()

    class Meta(ProteinBaseSerializer.Meta):
        meta_fields = ('descriptions','scores_count')
        fields = ProteinBaseSerializer.Meta.fields + meta_fields
        read_only_fields = ProteinBaseSerializer.Meta.read_only_fields + meta_fields

    def get_descriptions(self, obj):
        if (obj.description):
            return obj.description_list
        return []


class ProteinSerializerExtendedScoresCount(ProteinSerializerExtended):
    class Meta(ProteinSerializerExtended.Meta):
        meta_fields = scores_count
        fields = ProteinSerializerExtended.Meta.fields + meta_fields
        read_only_fields = ProteinSerializerExtended.Meta.read_only_fields + meta_fields


#### Metabolite ####
class MetaboliteBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metabolite
        meta_fields = ('name', 'external_id')
        fields = meta_fields
        read_only_fields = meta_fields


class MetaboliteLightSerializer(MetaboliteBaseSerializer):
    pathway_group = serializers.SerializerMethodField()
    pathway_subgroup = serializers.SerializerMethodField()

    class Meta(MetaboliteBaseSerializer.Meta):
        model = Metabolite
        meta_fields = ('pathway_group','pathway_subgroup')
        fields =  MetaboliteBaseSerializer.Meta.fields + meta_fields
        read_only_fields = MetaboliteBaseSerializer.Meta.read_only_fields + meta_fields

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


# /!\ Need to sort out the pathway_group/subgroup /!\
class MetaboliteSerializer(MetaboliteBaseSerializer):
    synonyms = serializers.SerializerMethodField()
    # pathway_group = PathwaySerializer(many=False, read_only=True)
    # pathway_subgroup = PathwaySerializer(many=False, read_only=True)

    class Meta(MetaboliteBaseSerializer.Meta):
        meta_fields = ('external_id_source', 'synonyms', 'xrefs') #,'pathway_group', 'pathway_subgroup')
        fields = MetaboliteBaseSerializer.Meta.fields + meta_fields
        read_only_fields = MetaboliteBaseSerializer.Meta.read_only_fields + meta_fields

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


class MetaboliteSerializerScoresCount(MetaboliteBaseSerializer):
    descriptions = serializers.SerializerMethodField()
    class Meta(MetaboliteBaseSerializer.Meta):
        meta_fields = ('descriptions', 'scores_count')
        fields = MetaboliteBaseSerializer.Meta.fields + meta_fields
        read_only_fields = MetaboliteBaseSerializer.Meta.read_only_fields + meta_fields

    def get_descriptions(self, obj):
        if (obj.description):
            return obj.description_list
        return []

class MetaboliteSerializerExtendedScoresCount(MetaboliteSerializerExtended):
    class Meta(MetaboliteSerializerExtended.Meta):
        meta_fields = scores_count
        fields = MetaboliteSerializerExtended.Meta.fields + meta_fields
        read_only_fields = MetaboliteSerializerExtended.Meta.read_only_fields + meta_fields


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

    class Meta:
        model = Score
        meta_fields = ('id', 'name', 'trait_reported', 'trait_reported_id', 'method_name', 'method_params',
                       'dataset_id', 'dataset_name', 'publication', 'platform', 'tissue',
                       'genes', 'transcripts', 'proteins', 'metabolites',
                       'variants_number', 'variants_interactions', 'variants_genomebuild',
                       'comment', 'license')
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


class ScorePlotSerializer(serializers.ModelSerializer):
    genes = GeneBaseSerializer(many=True, read_only=True)
    transcripts = TranscriptBaseSerializer(many=True, read_only=True)
    proteins = ProteinBaseSerializer(many=True, read_only=True)
    metabolites = MetaboliteBaseSerializer(many=True, read_only=True)

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
        ''' Get Tissue model '''
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
    tissue = serializers.SerializerMethodField()
    platform_version = serializers.SerializerMethodField()

    class Meta:
        model = Score
        meta_fields = ('id','name','variants_number','dataset_id','dataset_name','platform_version','publication','tissue','ancestry')
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

    def get_tissue(self, obj):
        ''' Get Tissue model '''
        tissue = obj.dataset.tissue
        return TissueSerializer(tissue, many=False, read_only=True).data


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


###################
#### Phenotype ####
###################

class PhenotypeSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField('get_categories')
    class Meta:
        model = Phenotype
        meta_fields = ('id', 'label', 'description', 'category', 'url')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_categories(self, obj):
        return obj.categories_list


class PhenotypeSerializerExtended(PhenotypeSerializer):
    class Meta(PhenotypeSerializer.Meta):
        meta_fields = ('traits_reported',)
        fields = PhenotypeSerializer.Meta.fields + meta_fields
        read_only_fields = PhenotypeSerializer.Meta.read_only_fields + meta_fields


class PhenotypeSerializerScoresCount(PhenotypeSerializerExtended):
    class Meta(PhenotypeSerializerExtended.Meta):
        meta_fields = ('phewas_count',)
        fields = PhenotypeSerializerExtended.Meta.fields + meta_fields
        read_only_fields = PhenotypeSerializerExtended.Meta.read_only_fields + meta_fields


class ScorePheWASSerializer(serializers.ModelSerializer):
    score = ScoreLightSerializer(many=False,read_only=True)
    phenotypes = PhenotypeSerializer(many=True,read_only=True)
    samples = SampleSerializer(many=True,read_only=True)
    publication = PublicationSerializer(many=False,read_only=True)
    data_values = serializers.SerializerMethodField('get_data_values')

    class Meta:
        model = ScorePheWAS
        meta_fields = ('score','phenotypes','samples','publication','trait_reported','method_description','ancestry',
                       'data_values','adjusted_pvalue_method','variants_number_used','variants_fraction_found')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_data_values(self, obj):
        return obj.values_dict


######################
#### Applications ####
######################

class PhenotypeOldSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhenotypeOld
        meta_fields = ('id','name','category','source')
        fields = meta_fields
        read_only_fields = meta_fields


class PhenotypeOldSerializerScoresCount(PhenotypeOldSerializer):
    class Meta(PhenotypeOldSerializer.Meta):
        meta_fields = scores_count
        fields = PhenotypeOldSerializer.Meta.fields + meta_fields
        read_only_fields = PhenotypeOldSerializer.Meta.read_only_fields + meta_fields


class PhenotypeOldSerializerExtended(PhenotypeOldSerializerScoresCount):
    # child_phenotype = PhenotypeOldSerializer(many=True,read_only=True)
    child_phenotype = serializers.SerializerMethodField()

    class Meta(PhenotypeOldSerializerScoresCount.Meta):
        meta_fields = ('child_phenotype',)
        fields = PhenotypeOldSerializerScoresCount.Meta.fields + meta_fields
        read_only_fields = PhenotypeOldSerializerScoresCount.Meta.read_only_fields + meta_fields

    def get_child_phenotype(self, obj):
        ''' Sort phenotype child terms by their IDs '''
        children = obj.child_phenotype.prefetch_related('phenotype_score').order_by('id')
        return PhenotypeOldSerializerScoresCount(children, many=True).data


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
    phenotype = PhenotypeOldSerializer(many=False,read_only=True)
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
    phenotype = PhenotypeOldSerializerScoresCount(many=False,read_only=True)

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

#     class Meta:
#         model = Score
#         meta_fields = ('id', 'name', 'trait_reported', 'trait_reported_id', 'method_name', 'method_params',
#                        'publication', 'platform', 'score_performance', 'genes', 'transcripts', 'proteins', 'metabolites',
#                        'variants_number', 'variants_interactions', 'variants_genomebuild',)
#         fields = meta_fields
#         read_only_fields = meta_fields


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