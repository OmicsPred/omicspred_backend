import os
# import pandas as pd
import logging
from imports.omicspred.spreadsheets.spreadsheet import CohortSpreadSheet, PublicationSpreadSheet, ScoreSpreadSheet, SamplePerformanceSpreadSheet
from imports.omicspred.models.species import SpeciesData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('spreadsheet parsing')

cwd = os.getcwd()

class MetadataTemplate():

    # empty_template = './imports/templates/OmicsPred_Submission_Template.xlsx'
    loc_schema = f'./imports/templates/TemplateColumns2Models.xlsx'

    default_license = 'Creative Commons Attribution 4.0 International (CC BY 4.0)'

    default_species = 'Homo sapiens'

    def __init__(self, file_loc:str, license:str=None):
        self.file_loc = file_loc
        self.parsed_publication = None
        self.parsed_scores = {}
        self.parsed_cohorts = {}
        self.parsed_sample_performance = {}
        self.parsed_datasets = {}
        self.species = None
        # self.parsed_samples_scores = []
        # self.parsed_samples_testing = []
        # self.parsed_samples = []
        # self.parsed_performances = []
        self.spreadsheet_names = {
            'Publication': 'Publication Information',
            'Score': 'Score Information',
            'Sample': 'Sample Information & Performanc', # <= Might need to fix the missing "e"
            'Cohort': 'Cohort Information'
        }
        if license:
            self.license = license if license else self.default_license

        self.report = { 'error': {}, 'warning': {}, 'import': {} }


    def read_curation(self,dataset_prefix:str=''):
        ''' Read metadata file and store the spreadsheets into pandas DataFrames. '''


        loc_excel = self.file_loc
        if loc_excel != None:

            omics_type = 'Transcriptomics'

            # Species
            species_data = SpeciesData(self.default_species)
            self.species = species_data.create_model()

            # Cohort spreadsheet
            cohort_spreadsheet = CohortSpreadSheet(loc_excel,self.loc_schema, self.spreadsheet_names['Cohort'],omics_type)
            cohort_spreadsheet.extract_data()
            self.parsed_cohorts = cohort_spreadsheet.export_parser_data()

            # Publication spreadsheet
            publication_spreadsheet = PublicationSpreadSheet(loc_excel,self.loc_schema, self.spreadsheet_names['Publication'],omics_type)
            publication_spreadsheet.extract_data()
            publication_data = publication_spreadsheet.export_parser_data()
            self.parsed_publication = list(publication_data.values())[0]

            # Score spreadsheet (including Platform and Tissue)
            score_spreadsheet = ScoreSpreadSheet(loc_excel, self.loc_schema, self.spreadsheet_names['Score'], omics_type, self.parsed_publication, self.license, self.species, dataset_prefix)
            score_spreadsheet.extract_data()
            self.parsed_scores = score_spreadsheet.export_parser_data()
            self.parsed_datasets = score_spreadsheet.export_datasets()

            # Sample and Performance Metrics spreadsheet
            sample_performance_spreadsheet = SamplePerformanceSpreadSheet(loc_excel,self.loc_schema, self.spreadsheet_names['Sample'],omics_type,self.parsed_cohorts)
            sample_performance_spreadsheet.extract_data()
            self.parsed_sample_performance = sample_performance_spreadsheet.export_parser_data()
            
        else:
            self.report_error('Global', "Missing spreadsheet file!")
            exit()


    def import_curation(self):

        print("- Import datasets")
        dataset_models = {}
        dataset_samples = {}
        for dataset_tag in self.parsed_datasets.keys():
            dataset_data = self.parsed_datasets[dataset_tag]
            dataset_model = dataset_data.create_model()
            dataset_models[dataset_tag] = dataset_model
            dataset_samples[dataset_model.id] = {
                'dataset': dataset_model,
                'sample_training': set(),
                'sample_validation': set()
            }

        print("- Import scores")
        score_models = {}
        for score_name in self.parsed_scores.keys():
            score_data = self.parsed_scores[score_name]
            # Add Dataset model to ScoreData
            dataset_tag = score_data.get_dataset_tag()
            if dataset_tag in dataset_models.keys():
                score_data.add_dataset_model(dataset_models[dataset_tag])
            score_model = score_data.create_model()
            score_models[score_name] = score_model


        print("- Import Samples and Performance Metrics")
        for score_name in self.parsed_sample_performance.keys():
            if not score_name in score_models.keys():
                print(f"ERROR: can't find Sample/Performance for the score '{score_name}'")
                continue
            score_model = score_models[score_name]
            dataset_model =  score_model.dataset
            for sp_parsed_data in self.parsed_sample_performance[score_name]:
                # Create Sample model
                sample_model = None
                sample_data = sp_parsed_data['sample']
                if sample_data:
                    sample_model = sample_data.create_model()
                # Performance and Performance Metrics
                performance_data = sp_parsed_data['performance']
                performance_data.add_score_model(score_model)
                performance_data.add_sample_model(sample_model)
                performance_data.add_dataset_model(dataset_model)
                if performance_data:
                    performance_model = performance_data.create_model()
                    if performance_model:
                        if performance_model.eval_type == 'T':
                            dataset_samples[dataset_model.id]['sample_training'].add(sample_model)
                        else:
                            dataset_samples[dataset_model.id]['sample_validation'].add(sample_model)

        # Link samples to Datasets 
        print("- Link Samples to Datasets")
        for dataset_id in dataset_samples.keys():
            dataset_model = dataset_samples[dataset_id]['dataset']
            if dataset_samples[dataset_id]['sample_training']:
                for sample_training in dataset_samples[dataset_id]['sample_training']:
                    dataset_model.samples_training.add(sample_training)
            if dataset_samples[dataset_id]['sample_validation']:
                for sample_validation in dataset_samples[dataset_id]['sample_validation']:
                    dataset_model.samples_validation.add(sample_validation)
            dataset_model.save()


            # # Add Dataset model to ScoreData
            # dataset_tag = score_data.get_dataset_tag()
            # if dataset_tag in dataset_models.keys():
            #     score_data.add_dataset_model(dataset_models[dataset_tag])
            # score_model = score_data.create_model()
            # score_models[score_name] = score_model
        # Datasets
        # - Create/Add Publication
        # - Create/Add PlatformMaster
        # - Create/Add Platform
        # - Create/Add Tissue
        # Link Datasets to ScoreData

        # Scores
        # - Create/Add Gene(s)
        # - Create/Add Protein(s)
        # - Create/Add Metabolite(s)

        # Performance
        # - Create/Add Sample -> Create/Add Cohort(s)
        # - Create/Add Metrics
        # Link to Dataset


# class RNAseqParser():

#     def __init__(self, data_info:dict):
#         self.study = data_info['name']
#         self.study_info = data_info['study_info']
#         self.gwas_data = data_info['gwas_data']
#         self.filepath = data_info['filepath']
#         self.platform = data_info['platform']
#         self.omicstype = data_info['type']
#         self.samples = data_info['samples_info']
#         self.publication = data_info['publication']
#         self.genomebuild = data_info['genomebuild']


#     def parse_performance_metric(self,score,efo,data_values,cohort_data):
#         ''' Parse performance and metric data '''
#         sample = None
#         extra = None
#         performance_model = None

#         cohort_name = cohort_data['name']
#         ancestry = cohort_data['ancestry']
#         type = cohort_data['vtype']

#         for sample_info in self.samples:
#             if sample_info['cohort'] == cohort_name and sample_info['ancestry'] == ancestry:
#                 sample = sample_info['sample']
#                 extra = sample_info['entities_count']+' genes'
#         if sample:
#             gwas_info = {}
#             platform_name = self.platform.name
#             gwas_data = self.gwas_data.data
#             if platform_name in gwas_data.keys():
#                 if cohort_name in gwas_data[platform_name].keys():
#                     gwas_info = gwas_data[platform_name][cohort_name]

#             performance_data = PerformanceData(score,self.publication,sample,self.platform,efo,type,gwas_info,extra)
#             performance_data.add_metric(data_values)
#             performance_model = performance_data.create_model()

#         return performance_model


#     def parse_data(self):
#         df = pd.read_csv(self.filepath)
#         for index, row in df.iterrows():
#             # Gene info
#             gene_id = row['Ensembl ID']
#             gene_name = row['Gene']
#             # Score info
#             score_id = row['OMICSPRED ID']
#             variants_number = row['#SNP']

#             print(f"- {score_id} | {gene_id}")

#             # Gene model
#             gene_data = GeneData(external_id=gene_id,name=gene_name)
#             gene_model = gene_data.create_model()

#             # EFO model
#             efo_data = EFOData(self.study_info['tissue'])
#             efo_model = efo_data.create_model()

#             # Score model
#             method_name = self.study_info['method_name']
#             score_data = ScoreData(score_id,variants_number,self.publication,self.platform,self.genomebuild,method_name)
#             score_model = score_data.create_model()
#             score_model.save()
#             score_model.genes.add(gene_model)
#             # score_model.efos.add(measurement_context_model)
#             score_model.save()


#             # Performance & Metric models
#             # - Training
#             cohort_internal_label = self.study_info['internal_label']
#             cohort_internal = self.study_info['internal_cohort']
#             training_values = {
#                 'R2': row[f'{cohort_internal_label}_R2'],
#                 'R2_pvalue': row[f'{cohort_internal_label}_R2_pvalue'],
#                 'Rho': row[f'{cohort_internal_label}_Rho'],
#                 'Rho_pvalue': row[f'{cohort_internal_label}_Rho_pvalue']
#             }
#             cohort_entry = self.study_info['sample_cohort_info'][cohort_internal]
#             self.parse_performance_metric(score_model,efo_model,training_values,cohort_entry)

#             # - Validations
#             # cohort_info = {
#             #     'INTERVAL_Withheld_Set': {'name': 'INTERVAL withheld subset', 'ancestry': 'European', 'vtype': 'IV'},
#             # }
#             for cohort in self.study_info['sample_cohort_info'].keys():
#                 if cohort != cohort_internal:
#                     validation_values = {
#                         'R2': row[f'{cohort}_R2'],
#                         'R2_pvalue': row[f'{cohort}_R2_pvalue'],
#                         'Rho': row[f'{cohort}_Rho'],
#                         'Rho_pvalue': row[f'{cohort}_Rho_pvalue'],
#                         'MissingRate': row[f'{cohort}_MissingRate']
#                     }
#                     cohort_entry = self.study_info['sample_cohort_info'][cohort]
#                     self.parse_performance_metric(score_model,efo_model,validation_values,cohort_entry)
