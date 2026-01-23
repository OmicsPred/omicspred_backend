import pandas as pd
import logging
from imports.omicspred.models.cohort import CohortData
from imports.omicspred.models.dataset import DatasetData
from imports.omicspred.models.metric import MetricData
from imports.omicspred.models.molecular_trait import GeneData, ProteinData, MetaboliteData
from imports.omicspred.models.platform import PlatformMasterData, PlatformData
from imports.omicspred.models.performance import PerformanceData
from imports.omicspred.models.publication import PublicationData
from imports.omicspred.models.sample import SampleData
from imports.omicspred.models.score import ScoreData
from imports.omicspred.models.tissue import TissueData
from omicspred.models import Species

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('spreadsheet parsing')
# logger = logging.getLogger(__name__)


class SpreadSheet():

    def __init__(self,loc_excel:str, loc_schema:str, spreadsheet_name:str, data_type:str, header_rows:list=[0]):
        self.spreadsheet_name = spreadsheet_name
        self.data_type = data_type
        self.parsed_data = {}
        self.dataframe = pd.read_excel(loc_excel, sheet_name=self.spreadsheet_name, header=header_rows, index_col=0)
        # print(f">>> LOC SCHEMA: {loc_schema}")
        self.metadata_template_schema = pd.read_excel(loc_schema, sheet_name='Format', index_col=0)
        # logger = logging.getLogger('import')


    def get_model_field_from_schema(self, col, current_schema) -> list:
        '''
        Retrieve the model and field from the Template, that corresponds to the current spreadsheet column.
        e.g. "Score Name/ID" -> model: Score |  field: name
        - col: the current column selected
        - current_schema: the template, indexed by the "Column"
        Return types: list of Django model, string
        '''

        data_indexes = {
            "Pearson's correlation__p-value": 0,
            "Spearman's rank correlation__p-value": 1,
            'Additional validation performance metrics/details (multiple columns can be applied)': 2
        }
        col_label = None
        col_name = None
        model = None
        field = None
        # Multi-row header
        if type(col) == tuple:
            col_len = len(col)
            # Third header
            if col_len >= 3:
                col2use = col[2]
                if col2use in current_schema.index:
                    col_name = col2use
                    col_label = f'{col[1]}__{col2use}'
                # Try with 2nd header (sometimes the 3rd header is labelled as "Unnamed...")
                elif col[1] in current_schema.index:
                    col_name = col[1]
                    col_label = col_name
            # Second header
            elif col_len >= 2:
                col2use = col[1]
                if col2use in current_schema.index:
                    col_name = col2use
                    col_label = col_name
                    # if col_name in data_indexes.keys():
                    #     data = current_schema.loc[col_name][:2]
                    #     model, field = data.iloc[data_indexes[col_name]][:2]
            # First header
            elif col[0] in current_schema.index:
                col_name = col[0]
                col_label = col_name
                # model, field = current_schema.loc[col[0]][:2]
                # data = current_schema.loc[col[0]][:2]
                # print(f'COL0 {col[0]}: {current_schema.loc[col[0]][:2]} <<<')
                # print(f"DATA: {len(data)}")
        # Single-row header
        elif type(col) == str:
            if col in current_schema.index:
                col_name = col
                col_label = col_name

        if col_name:
            # print(f"- COLNAME: {col_label}")
            if col_label in data_indexes.keys():
                data = current_schema.loc[col_name][:2]
                model, field = data.iloc[data_indexes[col_label]][:2]
            else:
                model, field = current_schema.loc[col_name][:2]
        else:
            logger.error(f"Column '{col}' is not found in the metadata schema!")
            exit(1)
        return model, field


    def export_parser_data(self) -> dict:
        ''' Export parsed data '''
        return self.parsed_data



class CohortSpreadSheet(SpreadSheet):

    def __init__(self,loc_excel:str, loc_schema:str, spreadsheet_name:str, data_type:str):
        super().__init__(loc_excel, loc_schema,spreadsheet_name, data_type)
        self.spreadsheet_schema = self.metadata_template_schema.loc[spreadsheet_name].set_index('Column')


    def extract_data(self):
        ''' Extract cohort information and store it into objects. '''
        model = 'Cohort'
        logger.info(f"Start to parse the {model} spreadsheet")
        # Loop throught the rows (i.e. score)
        for cohort_name, cohort_info in self.dataframe.iterrows():
            parsed_cohort = CohortData(cohort_name, {'name_short': cohort_name})
            # Loop throught the columns
            for col, val in cohort_info.items():
                m, f = self.get_model_field_from_schema(col, self.spreadsheet_schema)
                if m == model:
                    parsed_cohort.add_data(f, val)
            self.parsed_data[cohort_name] = parsed_cohort



class PublicationSpreadSheet(SpreadSheet):

    def __init__(self,loc_excel:str, loc_schema:str, spreadsheet_name:str, data_type:str):
        super().__init__(loc_excel, loc_schema,spreadsheet_name, data_type)
        self.spreadsheet_schema = self.metadata_template_schema.loc[spreadsheet_name].set_index('Column')


    def extract_data(self):
        ''' Extract publication information and store it into an object. '''
        model = 'Publication'
        logger.info(f"Start to parse the {model} spreadsheet")
        pmid = None
        pub_info = self.dataframe.iloc[0]
        for col in pub_info.keys():
            # m, f = self.get_model_field_from_schema(col,self.spreadsheet_schema)
            m, f  = self.spreadsheet_schema.loc[col][:2]
            if f == 'pmid':
                pmid = pub_info[col]
                break
        if pmid:
            pub_data = PublicationData(pmid)
            pub_data.fetch_publication_information()
            self.parsed_data[pmid] = pub_data



class ScoreSpreadSheet(SpreadSheet):

    def __init__(self,loc_excel:str, loc_schema:str, spreadsheet_name:str, data_type:str,
                 publication:PublicationData, license:str, species:Species, dataset_prefix:str=''):
        super().__init__(loc_excel, loc_schema,spreadsheet_name, data_type,[0, 1])
        self.spreadsheet_schema = self.metadata_template_schema.loc[spreadsheet_name].set_index('Column')
        self.dataset_prefix = dataset_prefix
        self.publication = publication
        self.license = license
        self.species = species
        self.datasets = {}
        self.tissues = {}
        self.genes = {}
        self.proteins = {}
        self.metabolites = {}

    def export_datasets(self):
        return self.datasets

    def export_genes(self):
        return self.genes

    def export_proteins(self):
        return self.proteins

    def export_metabolites(self):
        return self.metabolites

    def extract_data(self):
        ''' Extract score information and store it into one or several ScoreData objects. '''
        model = 'Score'
        logger.info(f" Start to parse the {model} spreadsheet")
        scores_count = len(self.dataframe.index)
        s_count = 0
        distinct_rows = {}
        dataset_methods = set()
        # Loop throught the rows (i.e. score)
        for score_name, score_info in self.dataframe.iterrows():
            parsed_score = ScoreData({'name': score_name, 'license': self.license})
            s_count += 1
            if score_name not in distinct_rows.keys():
                distinct_rows[score_name] = 0
            distinct_rows[score_name] += 1
            if scores_count < 100:
                print(f"  # {score_name=}")
            elif str(s_count).endswith('0000'):
                print(f"  - {s_count} scores parsed")
            platform_master = None
            platform = None
            tissue = ''
            molecular_trait = {}
            # Loop throught the columns
            for col, val in score_info.items():
                # print(f"  >> {col}: {val}")
                if pd.isnull(val) is False:
                    # Map to schema
                    m, f = self.get_model_field_from_schema(col, self.spreadsheet_schema)
                    # print(f"  >> {m}: {f} | {val}")
                    if m == model:
                        parsed_score.add_data(f, val)
                        # print(f"  - {f}: {val}")
                        # WARNING: At the moment only deals with 1 reported molecular trait
                        if f == 'trait_reported':
                            molecular_trait['name'] = val
                        elif f == 'trait_reported_id':
                            molecular_trait['id'] = val
                    # Add Tissue
                    elif m == 'EFO' and f == 'id':
                        if val in self.tissues.keys():
                            tissue = self.tissues[val]
                        else:
                            tissue = TissueData(val)
                            tissue.fetch_tissue_information()
                            self.tissues[val] = tissue
                        # print(f"  - Tissue: {','.join(efo_list)}")
                        # parsed_score.add_other_model('efo',tissues_list)
                    # Add Platform Master
                    elif m == 'PlatformMaster' and f == 'name':
                        # Fetch/build PlatformMaster
                        platform_master = PlatformMasterData(val,self.data_type)
                        # parsed_score.add_other_model('platform_master',platform_master)
                    # Add Platform (version)
                    elif m == 'Platform' and f == 'version':
                        # Fetch/build Platform
                        platform = PlatformData(platform_master,str(val))
                        # parsed_score.add_other_model('platform',platform)
                        # print(f"  - Platform: {val} | {platform_master}")
            score_method = parsed_score.get_score_method_name()
            if score_method:
                dataset_methods.add(score_method)
            if not platform:
                platform = PlatformData(platform_master,None)
    
            # Add molecular trait objects (gene, protein, metabolite)
            if molecular_trait:

                mt_id = None
                if 'id' in molecular_trait.keys():
                    mt_id = molecular_trait['id'].split('.')[0]

                mt_name = None
                if 'name' in molecular_trait.keys():
                    mt_name = molecular_trait['name']

                if self.data_type == 'Transcriptomics':
                    gene_data = GeneData(mt_id, mt_name)
                    self.genes[gene_data.data_id] = gene_data
                    parsed_score.add_other_model('genes',[gene_data])
                    # print(f"  - Gene: {mt_id} | {mt_name}")
                elif self.data_type == 'Proteomics':
                    protein_data = ProteinData(mt_id, mt_name)
                    self.proteins[protein_data.data_id] = protein_data
                    parsed_score.add_other_model('proteins',[protein_data])
                elif self.data_type == 'Metabolomics':
                    metabolite_data = MetaboliteData(mt_id, mt_name)
                    self.metabolites[metabolite_data.data_id] = metabolite_data
                    parsed_score.add_other_model('metabolites',[metabolite_data])


            # Add/create dataset
            platform_version = platform.version if platform and platform.version else ''
            dataset_tag_suffix = tissue.id
            dataset_name_suffix = tissue.label

            ############ TEMP (for ARIC imports) ############ TODO -> to remove
            if score_name.endswith('_AA') or score_name.endswith('_EA'):
                score_components = score_name.rsplit('_', 1)
                dataset_tag_suffix = score_components[1]
                dataset_name_suffix = score_components[1]
            #################################################

            dataset_tag = f'{platform.name}_{platform_version}_{self.publication.pmid}_{dataset_tag_suffix}'
            if dataset_tag in self.datasets.keys():
                dataset = self.datasets[dataset_tag]
                dataset.add_score()
            else:
                dataset_name = ''
                if self.dataset_prefix != '':
                    dataset_name = self.dataset_prefix+' '
                dataset_name += dataset_name_suffix
                dataset = DatasetData(self.publication,platform,tissue,self.data_type,self.species,dataset_methods,dataset_name)
            self.datasets[dataset_tag] = dataset
            # print(f"  - Dataset id: {dataset_tag}")

            parsed_score.set_dataset_tag(dataset_tag)

            self.parsed_data[score_name] = parsed_score
        print(f"  - {s_count} scores parsed")
        for score, count in distinct_rows.items():
            if count > 1:
                print(f">>> Score {score}: {count} occurences")


class SamplePerformanceSpreadSheet(SpreadSheet):

    def __init__(self,loc_excel:str, loc_schema:str, spreadsheet_name:str, data_type:str, cohorts_data:dict):
        super().__init__(loc_excel, loc_schema,spreadsheet_name, data_type, [0, 1, 2])
        self.spreadsheet_schema = self.metadata_template_schema.loc[spreadsheet_name].set_index('Column')
        self.cohorts_data = cohorts_data

    def extract_data(self):
        ''' Extract sample and performance metrics information and store it into objects. '''
        model = 'Sample'
        logger.info(f" Start to parse the {model} spreadsheet")
        metric_types = {
            'r score': 'R2',
            'Rho score': 'Rho',
            "Pearson's correlation__p-value": 'R2',
            "Spearman's rank correlation__p-value": 'Rho'
        }
        metric_types_keys = metric_types.keys()
        # Loop throught the rows (i.e. score)
        for score_name, sample_info in self.dataframe.iterrows():
            cohorts = []
            sample_data = {}
            performance_data = {}
            metric_data = {}
            metric_type = None
            # Loop throught the columns
            for col, val in sample_info.items():
                # print(f"SamplePerformanceSpreadSheet  >> {col}: {val}")
                if pd.isnull(val) is False:
                    # Map to schema
                    m, f = self.get_model_field_from_schema(col, self.spreadsheet_schema)
                    # print(f"====> {m}: {f} | {val}")
                    if m == 'Sample':
                        # Sample age and sample age standard deviation
                        if f == 'sample_age':
                            val_str = str(val)
                            if '(' in val_str:
                                (age,age_sd) = val_str.split(' (')
                                age_sd = age_sd.replace(')','')
                                age = float(age) if '.' in age else int(age)
                                sample_data['sample_age'] = float(age)
                                sample_data['sample_age_sd'] = float(age_sd)
                            else:
                                sample_data['sample_age'] = val
                        # Cohorts
                        elif f == 'cohorts':
                            cohorts_list = val.split(',')
                            for cohort in cohorts_list:
                                if cohort in self.cohorts_data.keys():
                                    cohorts.append(self.cohorts_data[cohort])
                                else:
                                    print(f"Cohort '{cohort}' is missing in the Cohort Information spreadsheet")
                            sample_data['cohorts'] = cohorts
                        # Other
                        else:
                            sample_data[f] = val
                            # print(f">> Sample {f}: {val}")
                    elif m == 'Performance':
                        performance_data[f] = val.strip()
                    elif m == 'Metric':
                        # print(f":::> Metric: {col} | {f} | {val}")
                        if f == 'estimate':
                            col_len = len(col)
                            col_label = col[2] if col_len >= 3 else col[1]
                            if col_label in metric_types_keys:
                                metric_type = metric_types[col_label]
                                metric_data[metric_type] = { 'name': metric_type, f : val }
                        elif f == 'pvalue':
                            # Use metric_type from the estimate in the previous loop iteration
                            metric_data[metric_type][f] = val

            # Sample
            sample = SampleData(sample_data)

            # Metric
            metrics = []
            for m_type in metric_data.keys():
                metric = MetricData(metric_data[m_type])
                metrics.append(metric)
            # print(f"==> Metrics: {len(metrics)}")
            # Perforance
            # performance = PerformanceData(score_name, metrics)
            performance = PerformanceData()
            for metric in metrics:
                performance.add_metrics(metric)
            for p_key, p_val in performance_data.items():
                performance.add_data(p_key, p_val)
            # print(f"==> Performance Metrics: {performance.metrics}")

            # Take into account when there are more than 1 performance per score
            if not score_name in self.parsed_data.keys():
                self.parsed_data[score_name] = []
            self.parsed_data[score_name].append({
                'sample': sample,
                'performance': performance
                # 'metrics': metric_data
            })
            # print(f"#PM {score_name}")
            # print(self.parsed_data[score_name])