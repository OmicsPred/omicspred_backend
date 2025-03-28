import pandas as pd
from imports.omicspred.models.score import ScoreData
from imports.omicspred.models.performance import PerformanceData
from imports.omicspred.models.omics import GeneData
from imports.omicspred.models.tissue import EFOData


class RNAseqParser():

    def __init__(self, data_info:dict):
        self.study = data_info['name']
        self.study_info = data_info['study_info']
        self.gwas_data = data_info['gwas_data']
        self.filepath = data_info['filepath']
        self.platform = data_info['platform']
        self.omicstype = data_info['type']
        self.samples = data_info['samples_info']
        self.publication = data_info['publication']
        self.genomebuild = data_info['genomebuild']


    def parse_performance_metric(self,score,efo,data_values,cohort_data):
        ''' Parse performance and metric data '''
        sample = None
        extra = None
        performance_model = None

        cohort_name = cohort_data['name']
        ancestry = cohort_data['ancestry']
        type = cohort_data['vtype']

        for sample_info in self.samples:
            if sample_info['cohort'] == cohort_name and sample_info['ancestry'] == ancestry:
                sample = sample_info['sample']
                extra = sample_info['entities_count']+' genes'
        if sample:
            gwas_info = {}
            platform_name = self.platform.name
            gwas_data = self.gwas_data.data
            if platform_name in gwas_data.keys():
                if cohort_name in gwas_data[platform_name].keys():
                    gwas_info = gwas_data[platform_name][cohort_name]

            performance_data = PerformanceData(score,self.publication,sample,self.platform,efo,type,gwas_info,extra)
            performance_data.add_metric(data_values)
            performance_model = performance_data.create_model()

        return performance_model


    def parse_data(self):
        df = pd.read_csv(self.filepath)
        for index, row in df.iterrows():
            # Gene info
            gene_id = row['Ensembl ID']
            gene_name = row['Gene']
            # Score info
            score_id = row['OMICSPRED ID']
            variants_number = row['#SNP']

            print(f"- {score_id} | {gene_id}")

            # Gene model
            gene_data = GeneData(external_id=gene_id,name=gene_name)
            gene_model = gene_data.create_model()

            # EFO model
            efo_data = EFOData(self.study_info['tissue'])
            efo_model = efo_data.create_model()

            # Score model
            method_name = self.study_info['method_name']
            score_data = ScoreData(score_id,variants_number,self.publication,self.platform,self.genomebuild,method_name)
            score_model = score_data.create_model()
            score_model.save()
            score_model.genes.add(gene_model)
            # score_model.efos.add(measurement_context_model)
            score_model.save()


            # Performance & Metric models
            # - Training
            cohort_internal_label = self.study_info['internal_label']
            cohort_internal = self.study_info['internal_cohort']
            training_values = {
                'R2': row[f'{cohort_internal_label}_R2'],
                'R2_pvalue': row[f'{cohort_internal_label}_R2_pvalue'],
                'Rho': row[f'{cohort_internal_label}_Rho'],
                'Rho_pvalue': row[f'{cohort_internal_label}_Rho_pvalue']
            }
            cohort_entry = self.study_info['sample_cohort_info'][cohort_internal]
            self.parse_performance_metric(score_model,efo_model,training_values,cohort_entry)

            # - Validations
            # cohort_info = {
            #     'INTERVAL_Withheld_Set': {'name': 'INTERVAL withheld subset', 'ancestry': 'European', 'vtype': 'IV'},
            # }
            for cohort in self.study_info['sample_cohort_info'].keys():
                if cohort != cohort_internal:
                    validation_values = {
                        'R2': row[f'{cohort}_R2'],
                        'R2_pvalue': row[f'{cohort}_R2_pvalue'],
                        'Rho': row[f'{cohort}_Rho'],
                        'Rho_pvalue': row[f'{cohort}_Rho_pvalue'],
                        'MissingRate': row[f'{cohort}_MissingRate']
                    }
                    cohort_entry = self.study_info['sample_cohort_info'][cohort]
                    self.parse_performance_metric(score_model,efo_model,validation_values,cohort_entry)
