from rest_framework import serializers
from omicspred.models import *
from applications.models import *


#### Cohort ####
class CohortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Cohort
        # meta_fields = ('name_short', 'name_full', 'name_others', 'url')
        meta_fields = ('name_short', 'name_full', 'url')
        fields = meta_fields
        read_only_fields = meta_fields


#### Sample ####
class SampleSerializer(serializers.ModelSerializer):
    cohorts = CohortSerializer(many=True, read_only=True)

    class Meta:
        model = Sample
        meta_fields = ('sample_number', 'sample_percent_male', 'sample_age', 'sample_age_sd',
                    'ancestry_broad', 'ancestry_free', 'ancestry_country', 'ancestry_additional',
                    'source_gwas_catalog', 'source_pmid','source_doi','cohorts','cohorts_additional')#,'tissue_name')
        fields = meta_fields
        read_only_fields = meta_fields


#### EFO / Trait ####
class EFOSerializer(serializers.ModelSerializer):

    class Meta:
        model = EFO
        meta_fields = ('id', 'label', 'description', 'url', 'type')
        fields = meta_fields
        read_only_fields = meta_fields


#### Publication ####
class PublicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Publication
        meta_fields = ('title', 'doi', 'pmid', 'journal', 'firstauthor', 'date_publication')
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


#### Platform Additional ####
class DatasetLightSerializer(serializers.ModelSerializer):
    platform = PlatformSerializer(many=False, read_only=True)
    tissue = EFOSerializer(many=False, read_only=True)
    samples_training = SampleSerializer(many=True, read_only=True)
    samples_validation = SampleSerializer(many=True, read_only=True)

    class Meta:
        model = Dataset
        meta_fields = ('name', 'platform', 'scores_count', 'omics_count', 'omics_type',
                       'tissue', 'samples_training', 'samples_validation','scoring_files_urls')
        fields = meta_fields
        read_only_fields = meta_fields

class DatasetSerializer(DatasetLightSerializer):
    publication = PublicationSerializer(many=False, read_only=True)

    class Meta(DatasetLightSerializer.Meta):
        meta_fields = ('publication',)
        fields = meta_fields + DatasetLightSerializer.Meta.fields
        read_only_fields = meta_fields + DatasetLightSerializer.Meta.fields


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
class PathwaySerializer(serializers.ModelSerializer):
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
class GeneSerializer(serializers.ModelSerializer):
    descriptions = serializers.SerializerMethodField()
    class Meta:
        model = Gene
        meta_fields = ('name','external_id','external_id_source','synonyms', 'descriptions', 'biotype')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_descriptions(self, obj):
        if (obj.description):
            return obj.description_list
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
class ProteinSerializer(serializers.ModelSerializer):
    descriptions = serializers.SerializerMethodField()
    class Meta:
        model = Protein
        meta_fields = ('name','external_id','external_id_source','descriptions')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_descriptions(self, obj):
        if (obj.description):
            return obj.description_list
        return []


class ProteinSerializerExtended(ProteinSerializer):
    gene = GeneSerializer(many=False, read_only=True)
    pathways = serializers.SerializerMethodField('get_pathways')

    class Meta(ProteinSerializer.Meta):
        meta_fields = ('gene','pathways')
        fields = ProteinSerializer.Meta.fields + meta_fields
        read_only_fields = ProteinSerializer.Meta.read_only_fields + meta_fields

    def get_pathways(self, obj):
        pathways = []
        # Pathways
        if obj.gene:
            for pathway in obj.gene.pathways.prefetch_related('superpathways').all():
                pathway_entry = {}
                for field in PathwaySerializer.Meta.fields:
                    # Superpathways
                    if field == 'superpathways':
                        sp_pathways = []
                        superpathways = getattr(pathway, field)
                        for superpathway in superpathways.all():
                            sp_pathway_entry = {}
                            for sp_field in SuperPathwaySerializer.Meta.fields:
                                sp_pathway_entry[sp_field] = getattr(superpathway, sp_field)
                            sp_pathways.append(sp_pathway_entry)
                        pathway_entry[field] = sp_pathways
                    else:
                        pathway_entry[field] = getattr(pathway, field)
                pathways.append(pathway_entry)
        return pathways


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

# /!\ No inheritance yet - need to sort out the pathway_group/subgroup /!\
class MetaboliteSerializer(serializers.ModelSerializer):
    # pathway_group = PathwaySerializer(many=False, read_only=True)
    # pathway_subgroup = PathwaySerializer(many=False, read_only=True)

    class Meta:
        model = Metabolite
        meta_fields = ('name', 'external_id', 'external_id_source', 'synonyms', 'xrefs') #,'pathway_group', 'pathway_subgroup')
        fields = meta_fields
        read_only_fields = meta_fields


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


#### Pathway - Extended (with genes and metabolites) ####
class PathwaySerializerNewExtended(PathwaySerializer):
    # superpathways = SuperPathwaySerializer(many=True, read_only=True)
    genes = GeneSerializerScoresCount(source='pathway_genes', many=True, read_only=True)
    metabolites = MetaboliteSerializerScoresCount(source='pathway_metabolites', many=True, read_only=True)
    class Meta(PathwaySerializer.Meta):
        meta_fields = ('genes', 'metabolites')
        # meta_fields = ('superpathways', 'genes', 'metabolites')
        fields = PathwaySerializer.Meta.fields + meta_fields
        read_only_fields = PathwaySerializer.Meta.read_only_fields + meta_fields


#### Score ####
class ScoreSerializer(serializers.ModelSerializer):
    # publication = PublicationSerializer(many=False, read_only=True)
    # platform = PlatformSerializer(many=False, read_only=True)
    publication = serializers.SerializerMethodField()
    platform = serializers.SerializerMethodField()

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
                       'variants_number', 'variants_interactions', 'variants_genomebuild', 'license')#, 'date_release')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_publication(self, obj):
        ''' Get Publication model '''
        publication = obj.dataset.publication
        return PublicationSerializer(publication, many=False, read_only=True).data

    def get_platform(self, obj):
        ''' Get Publication model '''
        platform = obj.dataset.platform
        return PlatformSerializer(platform, many=False, read_only=True).data


class ScorePathwaySerializer(ScoreSerializer):
    genes = GeneSerializerExtended(many=True, read_only=True)
    metabolites = MetaboliteSerializerExtended(many=True, read_only=True)

    class Meta(ScoreSerializer.Meta):
        fields = ScoreSerializer.Meta.fields
        read_only_fields = ScoreSerializer.Meta.read_only_fields


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


#### Metric ####
class MetricSerializer(serializers.ModelSerializer):

    class Meta:
        model = Metric
        meta_fields = ('name', 'name_short', 'performance_type', 'estimate', 'pvalue')
        fields = meta_fields
        read_only_fields = meta_fields


#### Performance ####
class PerformanceSerializer(serializers.ModelSerializer):
    # publication = PublicationSerializer(many=False, read_only=True)
    # platform = PlatformSerializer(many=False, read_only=True)
    publication = serializers.SerializerMethodField()
    platform = serializers.SerializerMethodField()
    sample = SampleSerializer(many=False, read_only=True)
    efo = EFOSerializer(many=False, read_only=True)

    evaluation_type = serializers.SerializerMethodField('get_eval_type_label')

    class Meta:
        model = Performance
        meta_fields = ('id', 'associated_opgs_id', 'publication', 'sample', 'platform', 'efo',
                       'performance_metrics', 'cohort_label',
                       'evaluation_type', 'performance_additional', 'covariates')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_publication(self, obj):
        ''' Get Publication model '''
        publication = obj.dataset.publication
        return PublicationSerializer(publication, many=False, read_only=True).data

    def get_platform(self, obj):
        ''' Get Publication model '''
        platform = obj.dataset.platform
        return PlatformSerializer(platform, many=False, read_only=True).data


    def get_eval_type_label(self, obj):
        return obj.get_eval_type_display()


class PerformanceLightSerializer(serializers.ModelSerializer):
    evaluation_type = serializers.SerializerMethodField('get_eval_type_label')
    class Meta:
        model = Performance
        meta_fields = ('performance_metrics', 'cohort_label','performance_additional', 'evaluation_type', 'covariates')
        fields = meta_fields
        read_only_fields = meta_fields

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
    class Meta:
        model = Score
        meta_fields = ('id','variants_number','performance_data')
        # meta_fields = ('id','variants_number','performance_range')
        fields = meta_fields
        read_only_fields = meta_fields


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


######################
#### Applications ####
######################

class PhecodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phecode
        meta_fields = ('id','name','category')
        fields = meta_fields
        read_only_fields = meta_fields


class PhecodeSerializerScoresCount(PhecodeSerializer):
    class Meta(PhecodeSerializer.Meta):
        meta_fields = ('scores_count',)
        fields = PhecodeSerializer.Meta.fields + meta_fields
        read_only_fields = PhecodeSerializer.Meta.read_only_fields + meta_fields


class PhecodeSerializerExtended(PhecodeSerializerScoresCount):

    # child_phecode = PhecodeSerializer(many=True,read_only=True)
    child_phecode = serializers.SerializerMethodField()

    class Meta(PhecodeSerializerScoresCount.Meta):
        meta_fields = ('child_phecode',)
        fields = PhecodeSerializerScoresCount.Meta.fields + meta_fields
        read_only_fields = PhecodeSerializerScoresCount.Meta.read_only_fields + meta_fields

    def get_child_phecode(self, obj):
        ''' Sort phecode child terms by their IDs '''
        children = obj.child_phecode.prefetch_related('phecode_score').order_by('id')
        return PhecodeSerializerScoresCount(children, many=True).data


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


class MolecularTraitApplicationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MolecularTraitApplications
        meta_fields = ('external_id','name','type')
        fields = meta_fields
        read_only_fields = meta_fields


class ScoreApplicationsSerializer(serializers.ModelSerializer):
    phecode = PhecodeSerializer(many=False,read_only=True)
    platform = PlatformApplicationsSerializer(many=False,read_only=True)
    cohort = CohortApplicationsSerializer(many=False,read_only=True)
    molecular_traits = MolecularTraitApplicationsSerializer(many=True,read_only=True)
    data_values = serializers.SerializerMethodField('get_data_values')
    class Meta:
        model = ScoreApplications
        meta_fields = ('score_id','phecode','platform','cohort','data_values','molecular_traits')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_data_values(self, obj):
        return obj.values_dict


class SampleApplicationsSerializer(serializers.ModelSerializer):
    phecode = PhecodeSerializerScoresCount(many=False,read_only=True)
    class Meta:
        model = SampleApplications
        meta_fields = ('sample_number','sample_cases','sample_percent_female','sample_age','sample_age_sd','phecode','platform_counts')
        fields = meta_fields
        read_only_fields = meta_fields




###############
#### TESTS ####
###############
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