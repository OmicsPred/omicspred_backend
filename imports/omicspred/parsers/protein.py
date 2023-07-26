import pandas as pd
import numpy as np
from imports.omicspred.models.score import ScoreData
from imports.omicspred.models.performance import PerformanceData
from imports.omicspred.models.omics import GeneData, ProteinData
from imports.omicspred.models.efo import EFOData
from omicspred.models import Platform



class ProteinParser():

    olink_neur_label = 'Olink (NEUR)'
    olink_other_label = 'Olink (INF-1, CVD-2, CVD-3)'

    def __init__(self, data_info:dict):
        self.study = data_info['name']
        self.study_info = data_info['study_info']
        self.gwas_data = data_info['gwas_data']
        self.filepath = data_info['filepath']
        self.platform = data_info['platform']
        self.protein_platform = data_info['protein_platform'][self.olink_neur_label]
        self.omicstype = data_info['type']
        self.samples = data_info['samples_info']
        self.publication = data_info['publication']
        self.genomebuild = data_info['genomebuild']
        self.sep = ';' # Olink
        if self.platform.name == 'Somalogic':
            self.sep = '|'


    def parse_performance_metric(self,score,efo,data_values,cohort_data,in_olink_neur):
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
            # print(f'+ {platform_name} / {cohort_name}')
            for platform_label in gwas_data.keys():
                if platform_name == 'Olink':
                    if self.olink_neur_label:
                        platform_name == self.olink_neur_label
                    else:
                        platform_name = self.olink_other_label
                    if cohort_name in gwas_data[platform_name].keys():
                        gwas_info = gwas_data[platform_name][cohort_name]
                        break
                elif platform_name == platform_label:
                    if cohort_name in gwas_data[platform_name].keys():
                        gwas_info = gwas_data[platform_name][cohort_name]
                        break


            performance_data = PerformanceData(score,self.publication,sample,self.platform,efo,type,gwas_info,extra)
            performance_data.add_metric(data_values)
            performance_model = performance_data.create_model()

        return performance_model


    def parse_data(self):
        df = pd.read_csv(self.filepath)

        protein_platform = []


        for index, row in df.iterrows():
            # Protein info
            protein_names = []
            protein_ids = []
            protein_name_entry = row['Protein']
            protein_id_entry = row['UniProt ID']
            if protein_name_entry and protein_name_entry not in [None,np.nan,'nan','']:
                protein_names = protein_name_entry.split(self.sep)
            if protein_id_entry and protein_id_entry not in [None,np.nan,'nan','']:
                protein_ids = protein_id_entry.split(self.sep)

            # Gene info
            gene_names = []
            gene_name_entry = row['Gene']
            if gene_name_entry and gene_name_entry not in [None,np.nan,'nan','']:
                gene_names = gene_name_entry.split(self.sep)

            # Score info
            score_id = row['OMICSPRED ID']
            score_name = None
            if 'SOMAscan ID' in row:
                score_name = row['SOMAscan ID']
            variants_number = row['#SNP']

            print(f"- {score_id} | {','.join(protein_ids)} | {','.join(gene_names)}")

            # Gene model
            gene_models = []
            for gene_name in gene_names:
                gene_data = GeneData(name=gene_name)
                gene_model = gene_data.create_model()
                gene_models.append(gene_model)

            # Protein model
            protein_models = []
            in_olink_neur = False
            if protein_ids:
                for index,protein_id in enumerate(protein_ids):
                    idx = 0
                    if len(protein_ids) == len(protein_names):
                        idx = index
                    protein_data = ProteinData(name=protein_names[idx], external_id=protein_id)
                    protein_model = protein_data.create_model()
                    protein_models.append(protein_model)
                    if protein_id in self.protein_platform:
                        in_olink_neur = True
            else:
                protein_data = ProteinData(name=protein_names[0])
                protein_model = protein_data.create_model()
                protein_models.append(protein_model)

            # EFO model
            efo_data = EFOData(self.study_info['tissue'])
            efo_model = efo_data.create_model()

            # Score model
            method_name = self.study_info['method_name']
            score_data = ScoreData(score_id,variants_number,self.publication,self.platform,self.genomebuild,method_name,score_name)
            score_model = score_data.create_model()
            score_model.save()

            for gene_model in gene_models:
                score_model.genes.add(gene_model)
            for protein_model in protein_models:
                score_model.proteins.add(protein_model)
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
            self.parse_performance_metric(score_model,efo_model,training_values,cohort_entry,in_olink_neur)

            # - Validations
            for cohort in self.study_info['sample_cohort_info'].keys():
                if cohort != cohort_internal:
                    validation_values = {
                        'R2': row[f'{cohort}_R2'],
                        'R2_pvalue': row[f'{cohort}_R2_pvalue'],
                        'Rho': row[f'{cohort}_Rho'],
                        'MissingRate': row[f'{cohort}_MissingRate']
                    }
                    # Specific case for ORCADES which is missing the Rho_pvalue data
                    if cohort != 'ORCADES':
                        validation_values['Rho_pvalue'] = row[f'{cohort}_Rho_pvalue']
                    cohort_entry = self.study_info['sample_cohort_info'][cohort]
                    self.parse_performance_metric(score_model,efo_model,validation_values,cohort_entry,in_olink_neur)
