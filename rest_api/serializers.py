from rest_framework import serializers
from omicspred.models import *
from applications.models import *

class CohortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Cohort
        # meta_fields = ('name_short', 'name_full', 'name_others', 'url')
        meta_fields = ('name_short', 'name_full', 'url')
        fields = meta_fields
        read_only_fields = meta_fields


# class CohortExtendedSerializer(CohortSerializer):
#
#     class Meta(CohortSerializer.Meta):
#         meta_fields = ('associated_pgs_ids',)
#         fields = CohortSerializer.Meta.fields + meta_fields
#         read_only_fields = CohortSerializer.Meta.read_only_fields + meta_fields


class SampleSerializer(serializers.ModelSerializer):
    cohorts = CohortSerializer(many=True, read_only=True)

    class Meta:
        model = Sample
        meta_fields = ('sample_number', 'sample_percent_male', 'sample_age', 'sample_age_sd',
                    'ancestry_broad', 'ancestry_free', 'ancestry_country', 'ancestry_additional',
                    'source_gwas_catalog', 'source_pmid','source_doi', 'cohorts_additional','cohorts','tissue_name')
        fields = meta_fields
        read_only_fields = meta_fields


class EFOSerializer(serializers.ModelSerializer):

    class Meta:
        model = EFO
        meta_fields = ('id', 'label', 'description', 'url', 'type')
        fields = meta_fields
        read_only_fields = meta_fields


class MetricSerializer(serializers.ModelSerializer):

    class Meta:
        model = Metric
        meta_fields = ('name', 'name_short', 'performance_type', 'estimate', 'pvalue')
        fields = meta_fields
        read_only_fields = meta_fields


class PublicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Publication
        meta_fields = ('title', 'doi', 'pmid', 'journal', 'firstauthor', 'date_publication')
        fields = meta_fields
        read_only_fields = meta_fields


class PlatformMasterSerializer(serializers.ModelSerializer):
    # versions = serializers.SerializerMethodField('get_versions')
    class Meta:
        model = PlatformMaster
        meta_fields = ('name', 'full_name', 'versions', 'technic', 'type', 'scores_count')
        fields = meta_fields
        read_only_fields = meta_fields

    # def get_versions(self, obj):
    #     versions = []
    #     print(obj.platform_version.all())
    #     for platform in obj.platform_version.all():
    #         if platform.version:
    #             versions.append(platform.version)
    #     return sorted(versions)


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


class PlatformAdditionalSerializer(serializers.ModelSerializer):
    publication = PublicationSerializer(many=False, read_only=True)
    platform = PlatformSerializer(many=False, read_only=True)
    tissue = EFOSerializer(many=False, read_only=True)
    samples_training = SampleSerializer(many=True, read_only=True)
    samples_validation = SampleSerializer(many=True, read_only=True)

    class Meta:
        model = PlatformAdditional
        meta_fields = ('publication', 'platform', 'scores_count', 'omics_count', 'omics_type', 'tissue',
                       'samples_training','samples_validation')
        fields = meta_fields
        read_only_fields = meta_fields


class PlatformAdditionalLightSerializer(serializers.ModelSerializer):
    platform = PlatformSerializer(many=False, read_only=True)
    tissue = EFOSerializer(many=False, read_only=True)
    samples_training = SampleSerializer(many=True, read_only=True)
    samples_validation = SampleSerializer(many=True, read_only=True)

    class Meta:
        model = PlatformAdditional
        meta_fields = ('platform', 'scores_count', 'omics_count', 'omics_type',
                       'tissue', 'samples_training', 'samples_validation')
        fields = meta_fields
        read_only_fields = meta_fields


class PublicationExtendedSerializer(PublicationSerializer):
    date_release = serializers.SerializerMethodField('get_date_released')
    platforms = PlatformAdditionalLightSerializer(many=True, read_only=True)

    class Meta(PublicationSerializer.Meta):
        model = Publication
        # meta_fields = ('date_release', 'authors','publication_pp')
        meta_fields = ('date_release', 'authors', 'platforms')
        fields = PublicationSerializer.Meta.fields + meta_fields
        read_only_fields = PublicationSerializer.Meta.read_only_fields + meta_fields

    def get_date_released(self, obj):
        return obj.date_released


class PathwaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pathway
        meta_fields = ('name', 'external_id', 'external_id_source')
        fields = meta_fields
        read_only_fields = meta_fields


class SuperPathwaySerializer(serializers.ModelSerializer):
    class Meta:
        model = SuperPathway
        meta_fields = ('name', 'external_id', 'external_id_source', 'synonyms', 'xrefs')
        fields = meta_fields
        read_only_fields = meta_fields


class PathwayNewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PathwayNew
        meta_fields = ('name', 'external_id', 'external_id_source', 'synonyms', 'xrefs')
        fields = meta_fields
        read_only_fields = meta_fields


class GeneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gene
        meta_fields = ('name', 'external_id', 'external_id_source', 'synonyms', 'biotype')
        fields = meta_fields
        read_only_fields = meta_fields


class GeneSerializerExtended(GeneSerializer):
    pathways = PathwayNewSerializer(many=True, read_only=True)

    class Meta(GeneSerializer.Meta):
        meta_fields = ('pathways',)
        fields = GeneSerializer.Meta.fields + meta_fields
        read_only_fields = GeneSerializer.Meta.read_only_fields + meta_fields


class TranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcript
        meta_fields = ('name', 'external_id', 'external_id_source')
        fields = meta_fields
        read_only_fields = meta_fields


class ProteinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Protein
        meta_fields = ('name', 'external_id', 'external_id_source')
        fields = meta_fields
        read_only_fields = meta_fields


class ProteinSerializerExtended(ProteinSerializer):
    gene = GeneSerializer(many=False, read_only=True)

    class Meta(ProteinSerializer.Meta):
        meta_fields = ('gene',)
        fields = ProteinSerializer.Meta.fields + meta_fields
        read_only_fields = ProteinSerializer.Meta.read_only_fields + meta_fields


class MetaboliteSerializer(serializers.ModelSerializer):
    pathway_group = PathwaySerializer(many=False, read_only=True)
    pathway_subgroup = PathwaySerializer(many=False, read_only=True)

    class Meta:
        model = Metabolite
        meta_fields = ('name', 'external_id', 'external_id_source', 'synonyms', 'xrefs','pathway_group', 'pathway_subgroup')
        fields = meta_fields
        read_only_fields = meta_fields


class MetaboliteSerializerExtended(MetaboliteSerializer):
    pathways = PathwayNewSerializer(many=True, read_only=True)

    class Meta(MetaboliteSerializer.Meta):
        meta_fields = ('description', 'pathways',)
        fields = MetaboliteSerializer.Meta.fields + meta_fields
        read_only_fields = MetaboliteSerializer.Meta.read_only_fields + meta_fields


class PathwaySerializerNewExtended(PathwayNewSerializer):
    superpathways = SuperPathwaySerializer(many=True, read_only=True)
    genes = GeneSerializer(source='pathway_genes', many=True, read_only=True)
    metabolites = MetaboliteSerializer(source='pathway_metabolites', many=True, read_only=True)
    class Meta(PathwayNewSerializer.Meta):
        meta_fields = ('superpathways', 'genes', 'metabolites')
        fields = PathwayNewSerializer.Meta.fields + meta_fields
        read_only_fields = PathwayNewSerializer.Meta.read_only_fields + meta_fields


class ScoreSerializer(serializers.ModelSerializer):
    publication = PublicationSerializer(many=False, read_only=True)
    platform = PlatformSerializer(many=False, read_only=True)

    genes = GeneSerializer(many=True, read_only=True)
    transcripts = TranscriptSerializer(many=True, read_only=True)
    proteins = ProteinSerializer(many=True, read_only=True)
    metabolites = MetaboliteSerializer(many=True, read_only=True)
    # efos = EFOSerializer(many=True, read_only=True)

    # date_release = serializers.SerializerMethodField('get_date_released')

    class Meta:
        model = Score
        meta_fields = ('id', 'name', 'trait_reported', 'trait_reported_id', 'method_name', 'method_params',
                       'publication', 'platform', 'genes', 'transcripts', 'proteins', 'metabolites', #'efos',
                       'variants_number', 'variants_interactions', 'variants_genomebuild')#, 'date_release')
        fields = meta_fields
        read_only_fields = meta_fields

    # def get_date_released(self, obj):
    #     return obj.date_released


class ScorePlotSerializer(serializers.ModelSerializer):
    genes = GeneSerializer(many=True, read_only=True)
    transcripts = TranscriptSerializer(many=True, read_only=True)
    proteins = ProteinSerializer(many=True, read_only=True)
    metabolites = MetaboliteSerializer(many=True, read_only=True)

    class Meta:
        model = Score
        meta_fields = ('num', 'id', 'variants_number', 'genes', 'transcripts', 'proteins', 'metabolites')
        fields = meta_fields
        read_only_fields = meta_fields


class PerformanceSerializer(serializers.ModelSerializer):
    publication = PublicationSerializer(many=False, read_only=True)
    sample = SampleSerializer(many=False, read_only=True)
    platform = PlatformSerializer(many=False, read_only=True)
    efo = EFOSerializer(many=False, read_only=True)

    evaluation_type = serializers.SerializerMethodField('get_eval_type_label')

    class Meta:
        model = Performance
        meta_fields = ('id', 'associated_opgs_id','publication','sample', 'platform', 'efo',
                'performance_metrics', 'cohort_label',
                'evaluation_type', 'performance_additional', 'covariates')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_eval_type_label(self, obj):
        return obj.get_eval_type_display()


class PerformanceLightSerializer(serializers.ModelSerializer):
    sample = SampleSerializer(many=False, read_only=True)
    class Meta:
        model = Performance
        meta_fields = ('sample', 'performance_metrics', 'performance_additional', 'eval_type', 'covariates')
        fields = meta_fields
        read_only_fields = meta_fields


class PerformanceOnlySerializer(serializers.ModelSerializer):
    evaluation_type = serializers.SerializerMethodField('get_eval_type_label')
    class Meta:
        model = Performance
        meta_fields = ('performance_metrics', 'cohort_label','performance_additional', 'evaluation_type', 'covariates')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_eval_type_label(self, obj):
        return obj.get_eval_type_display()


class ScorePerformanceSerializer(ScoreSerializer):
    score_performance = PerformanceOnlySerializer(many=True, read_only=True)

    class Meta(ScoreSerializer.Meta):
        meta_fields = ('score_performance',)
        fields = ScoreSerializer.Meta.fields + meta_fields
        read_only_fields = ScoreSerializer.Meta.read_only_fields + meta_fields


###########
## TESTS ##
###########
class ScoreExtendedSerializer(serializers.ModelSerializer):
    publication = PublicationSerializer(many=False, read_only=True)
    platform = PlatformSerializer(many=False, read_only=True)

    genes = GeneSerializer(many=True, read_only=True)
    transcripts = TranscriptSerializer(many=True, read_only=True)
    proteins = ProteinSerializer(many=True, read_only=True)
    metabolites = MetaboliteSerializer(many=True, read_only=True)
    score_performance = PerformanceLightSerializer(many=True, read_only=True)

    date_release = serializers.SerializerMethodField('get_date_released')

    class Meta:
        model = Score
        meta_fields = ('id', 'name', 'trait_reported', 'trait_reported_id', 'method_name', 'method_params',
                       'publication', 'platform', 'score_performance', 'genes', 'transcripts', 'proteins', 'metabolites', #'efos',
                       'variants_number', 'variants_interactions', 'variants_genomebuild', 'date_release')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_date_released(self, obj):
        return obj.date_released


class OmicsScoreSerializer(serializers.ModelSerializer):
    publication = PublicationSerializer(many=False, read_only=True)
    platform = PlatformSerializer(many=False, read_only=True)

    metabolites = MetaboliteSerializer(many=True, read_only=True)
    score_performance = PerformanceLightSerializer(many=True, read_only=True)

    class Meta:
        model = Score
        meta_fields = ('id', 'name', 'trait_reported', 'trait_reported_id', 'method_name', 'method_params',
                    'publication', 'platform', 'score_performance',
                    'variants_number', 'variants_interactions', 'variants_genomebuild')
        fields = meta_fields
        read_only_fields = meta_fields


class MetaboliteScoreSerializer(OmicsScoreSerializer):
    metabolites = MetaboliteSerializer(many=True, read_only=True)

    class Meta(OmicsScoreSerializer):
        meta_fields = ('metabolites',)
        fields = OmicsScoreSerializer.Meta.fields + meta_fields
        read_only_fields = OmicsScoreSerializer.Meta.read_only_fields + meta_fields


class ProteinScoreSerializer(OmicsScoreSerializer):
    genes = GeneSerializer(many=True, read_only=True)
    proteins = ProteinSerializer(many=True, read_only=True)

    class Meta(OmicsScoreSerializer):
        meta_fields = ('genes', 'proteins')
        fields = OmicsScoreSerializer.Meta.fields + meta_fields
        read_only_fields = OmicsScoreSerializer.Meta.read_only_fields + meta_fields


class TranscriptScoreSerializer(OmicsScoreSerializer):
    genes = GeneSerializer(many=True, read_only=True)

    class Meta(OmicsScoreSerializer):
        meta_fields = ('genes',) # transcripts
        fields = OmicsScoreSerializer.Meta.fields + meta_fields
        read_only_fields = OmicsScoreSerializer.Meta.read_only_fields + meta_fields


# class OmicsPlotSerializer(serializers.ModelSerializer):
#     platform = PlatformSerializer(many=False, read_only=True)
#     score_performance = PerformanceLightSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = Score
#         meta_fields = ('platform', 'score_performance')
#         fields = meta_fields
#         read_only_fields = meta_fields
class OmicsPlotSerializer(serializers.ModelSerializer):
    platform = PlatformSerializer(many=False, read_only=True)
    sample = SampleSerializer(many=False, read_only=True)

    class Meta:
        model = Performance
        meta_fields = ('score_id', 'platform', 'sample', 'performance_metrics')
        fields = meta_fields
        read_only_fields = meta_fields

#### Table ####

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


class ProteinLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Protein
        meta_fields = ('name','external_id')
        fields = meta_fields
        read_only_fields = meta_fields


class GeneLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gene
        meta_fields = ('name','external_id')
        fields = meta_fields
        read_only_fields = meta_fields

# class PerformanceTestSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Performance
#         # meta_fields = ('score', 'score__metabolites', 'cohort_metrics')
#         meta_fields = ('cohort_metrics',)
#         fields = meta_fields
#         read_only_fields = meta_fields


class ScoreMetaboliteSerializer(serializers.ModelSerializer):
    metabolites = MetaboliteLightSerializer(many=True, read_only=True)
    class Meta:
        model = Score
        meta_fields = ('id','trait_reported','trait_reported_id','variants_number','metabolites','performance_data')
        fields = meta_fields
        read_only_fields = meta_fields


class ScoreProteinSerializer(serializers.ModelSerializer):
    proteins = ProteinLightSerializer(many=True, read_only=True)
    genes = GeneLightSerializer(many=True, read_only=True)
    class Meta:
        model = Score
        meta_fields = ('id','variants_number','proteins','genes','performance_data')
        fields = meta_fields
        read_only_fields = meta_fields


class ScoreTranscriptSerializer(serializers.ModelSerializer):
    genes = GeneLightSerializer(many=True, read_only=True)
    class Meta:
        model = Score
        meta_fields = ('id','variants_number','genes','performance_data')
        fields = meta_fields
        read_only_fields = meta_fields


##################
## Applications ##
##################

class PhecodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phecode
        meta_fields = ('id','name','category')
        fields = meta_fields
        read_only_fields = meta_fields


class PhecodeSerializerExtended(PhecodeSerializer):

    # child_phecode = PhecodeSerializer(many=True,read_only=True)
    child_phecode = serializers.SerializerMethodField()

    class Meta(PhecodeSerializer.Meta):
        meta_fields = ('child_phecode',)
        fields = PhecodeSerializer.Meta.fields + meta_fields
        read_only_fields = PhecodeSerializer.Meta.read_only_fields + meta_fields

    def get_child_phecode(self, obj):
        ''' Sort phecode child terms by their IDs '''
        children = obj.child_phecode.order_by('id')
        return PhecodeSerializer(children, many=True).data


class PlatformApplicationsSerializer(PlatformSerializer):
    class Meta:
        model = PlatformApplications
        fields = PlatformSerializer.Meta.fields
        read_only_fields = PlatformSerializer.Meta.read_only_fields


class CohortApplicationsSerializer(CohortSerializer):
    class Meta:
        model = CohortApplications
        fields = CohortSerializer.Meta.fields
        read_only_fields = CohortSerializer.Meta.read_only_fields


class ScoreApplicationsSerializer(serializers.ModelSerializer):
    phecode = PhecodeSerializer(many=False,read_only=True)
    platform = PlatformApplicationsSerializer(many=False,read_only=True)
    cohort = CohortApplicationsSerializer(many=False,read_only=True)
    data_values = serializers.SerializerMethodField('get_data_values')
    class Meta:
        model = ScoreApplications
        meta_fields = ('id', 'score_id','omics_name','phecode','platform','cohort','data_values')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_data_values(self, obj):
        return obj.values_dict


class SampleApplicationsSerializer(serializers.ModelSerializer):
    phecode = PhecodeSerializer(many=False,read_only=True)
    class Meta:
        model = SampleApplications
        meta_fields = ('id','sample_number','sample_cases','sample_percent_female','sample_age','sample_age_sd','phecode','platform_counts')
        fields = meta_fields
        read_only_fields = meta_fields
