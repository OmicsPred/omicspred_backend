import pandas as pd
from imports.omicspred.models.score import ScoreData
from imports.omicspred.models.performance import PerformanceData
from imports.omicspred.models.omics import MetaboliteData, PathwayData
from imports.omicspred.models.tissue import EFOData



class MetaboliteParser():

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
            if performance_data.metrics:
                performance_model = performance_data.create_model()

        return performance_model


    def parse_data(self):
        df = pd.read_csv(self.filepath)

        # Nightingale
        meta_name_col = 'Biomarker Name'
        meta_gp_col = 'Group'
        meta_subgp_col = 'Subgroup'
        # Metabolonx
        if self.platform.name == 'Metabolon':
            meta_name_col = 'Biochemical Name'
            meta_gp_col = 'Super Pathway'
            meta_subgp_col = 'Sub Pathway'

        for index, row in df.iterrows():
            # Metabolite info
            metabolite_id = None
            if 'Metabolon ID' in row:
                metabolite_id = row['Metabolon ID']
            metabolite_name = row[meta_name_col]

            # Pathway info
            pathway = row[meta_gp_col]
            subpathway = row[meta_subgp_col]

            # Score info
            score_id = row['OMICSPRED ID']
            variants_number = row['#SNP']

            print(f"- {score_id} | {metabolite_name}")

            # Pathway model
            pathway_model = None
            if pathway:
                pathway_data = PathwayData(name=pathway)
                pathway_model = pathway_data.create_model()

            # Subpathway model
            subpathway_model = None
            if subpathway:
                subpathway_data = PathwayData(name=subpathway)
                subpathway_model = subpathway_data.create_model()

            # Metabolite model
            metabolite_data = MetaboliteData(
                name = metabolite_name,
                external_id = metabolite_id,
                pathway_group = pathway_model,
                pathway_subgroup = subpathway_model
            )
            metabolite_model = metabolite_data.create_model()

            # EFO model
            efo_data = EFOData(self.study_info['tissue'])
            efo_model = efo_data.create_model()

            # Score model
            method_name = self.study_info['method_name']
            score_data = ScoreData(score_id,variants_number,self.publication,self.platform,self.genomebuild,method_name)
            score_model = score_data.create_model()
            score_model.save()
            score_model.metabolites.add(metabolite_model)
            # score_model.efos.add(efo_model)
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
