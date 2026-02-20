import os.path, tarfile
import pandas as pd
import hashlib


fields_to_export = {
    'Cohort':
        [
            {'name': 'name_short', 'label': 'Cohort ID'},
            {'name': 'name_full', 'label': 'Cohort Name'},
            {'name': 'name_others', 'label': 'Previous/other/additional names'},
            {'name': 'url', 'label': 'Cohort link'}
        ],
    'Dataset': 
        [
            {'name': 'id', 'label': 'OmicsPred Dataset (OPD) ID'},
            {'name': 'name', 'label': 'Dataset Name'},
            {'name': 'omics_type', 'label': 'Omics Type' },
            {'name': 'method_name', 'label': 'Development Method'},
            {'name': 'scores_count', 'label': 'Scores Count'},
            {'name': 'platform__name', 'label': 'Platform Name'},
            {'name': 'platform__version', 'label': 'Platform Version'},
            {'name': 'tissue__id', 'label': 'Tissue ID'},
            {'name': 'tissue__label', 'label': 'Tissue Name'},
            {'name': 'species__name', 'label': 'Species'},
            {'name': 'license', 'label': 'License/Terms of Use'},
            {'name': 'file_url_scoring_files_pgsc_calc', 'label': 'Scoring files (pgsc_calc compatible)', 'skip_auto_import': True},
            {'name': 'file_url_scoring_files_hm_38', 'label': 'Harmonised scoring files (mapped to GRCh38)', 'skip_auto_import': True},
            {'name': 'file_url_scoring_files', 'label': 'Scoring files', 'skip_auto_import': True},
            {'name': 'file_url_predictdb', 'label': 'PredictDB', 'skip_auto_import': True},
            {'name': 'file_url_covariance', 'label': 'Covariance', 'skip_auto_import': True},
            {'name': 'file_url_validation_results', 'label': 'Validation data file', 'skip_auto_import': True},
            {'name': 'file_url_score_variant_info', 'label': 'Score variant info file', 'skip_auto_import': True},
            {'name': 'file_url_gwas_sumstats', 'label': 'GWAS summary stats files', 'skip_auto_import': True}
        ],
    'MolecularTrait':
        [
            {'name': 'external_id', 'label': 'Molecular Trait ID(s)'},
            {'name': 'name', 'label': 'Molecular Trait name(s)'},
        ],
    'Score':
        [
            {'name': 'id', 'label': 'OmicsPred ID'},
            {'name': 'name', 'label': 'Score Name'},
            {'name': 'trait_reported', 'label': 'Reported Trait'},
            {'name': 'trait_reported_id', 'label': 'Reported Trait ID'},
            {'name': 'method_name', 'label': 'Development Method'},
            {'name': 'method_params', 'label': 'Development Details/Relevant Parameters'},
            {'name': 'variants_genomebuild', 'label': 'Original Genome Build'},
            {'name': 'variants_number', 'label': 'Number of Variants'},
            {'name': 'genes__external_id', 'label': 'Gene ID(s)', 'skip_auto_import': True},
            {'name': 'genes__name', 'label': 'Gene name(s)', 'skip_auto_import': True},
            {'name': 'proteins__external_id', 'label': 'Protein ID(s)', 'skip_auto_import': True},
            {'name': 'proteins__name', 'label': 'Protein name(s)', 'skip_auto_import': True},
            {'name': 'metabolites__external_id', 'label': 'Metabolite ID(s)', 'skip_auto_import': True},
            {'name': 'metabolites__name', 'label': 'Metabolite name(s)', 'skip_auto_import': True},
            {'name': 'comment', 'label': 'Comment'},
            {'name': 'license', 'label': 'License/Terms of Use'}
        ],
    'Performance':
        [
            {'name': 'score__id', 'label': 'OmicsPred ID'},
            {'name': 'eval_type', 'label': 'Study stage'},
            {'name': 'covariates', 'label': 'Covariates'},
            {'name': 'sample__sample_number', 'label': 'Number of Individuals'},
            {'name': 'sample__sample_percent_male', 'label': 'Percent of Participants Who are Male'},
            {'name': 'sample__sample_age', 'label': 'Mean Sample Age'},
            {'name': 'sample__sample_age_sd', 'label': 'Standard Deviation of Age'},
            {'name': 'sample__ancestry_broad', 'label': 'Broad Ancestry Category'},
            {'name': 'cohorts', 'label': 'Cohort(s)', 'skip_auto_import': True},
            {'name': 'metrics_r2', 'label': 'R2', 'skip_auto_import': True},
            {'name': 'metrics_r2_pval', 'label': 'R2 - p-value', 'skip_auto_import': True},
            {'name': 'metrics_rho', 'label': 'Rho', 'skip_auto_import': True},
            {'name': 'metrics_rho_pval', 'label': 'Rho - p-value', 'skip_auto_import': True},
            {'name': 'metrics_match_rate', 'label': 'Match Rate', 'skip_auto_import': True}
        ],
    'Publication':
        [
            {'name': 'id', 'label': 'OmicsPred Publication (OPP) ID'},
            {'name': 'firstauthor', 'label': 'First Author'},
            {'name': 'title', 'label': 'Title'},
            {'name': 'journal', 'label': 'Journal Name'},
            {'name': 'date_publication', 'label': 'Publication Date'},
            {'name': 'authors', 'label': 'List of authors'},
            {'name': 'doi', 'label': 'digital object identifier (doi)'},
            {'name': 'pmid', 'label': 'PubMed ID (PMID)'}
        ]
}

dataset_files = [ x['name'] for x in fields_to_export['Dataset'] if x['name'].startswith('file_url_')]


#-----------------#
# Class OPExport #
#-----------------#

class OPExport:
    ''' Export each OmicsPred metadata in different Excel file (one per dataset). '''

    #---------------#
    # Configuration #
    #---------------#

    fields_to_include = fields_to_export

    extra_fields_to_include = [] # Need to be removed if not used
    # extra_fields_to_include = [
    #     'associated_score',
    #     'cohorts_list',
    #     'pub_doi_label',
    #     'pub_id',
    #     'pub_pmid_label',
    #     'sampleset_id',
    #     'study_stage',
    #     'trait_id',
    #     'trait_label',
    #     'ancestry_gwas',
    #     'ancestry_dev',
    #     'ancestry_eval'
    # ]

    # Data separator
    separator = '|'

    #-----------------#
    # General methods #
    #-----------------#

    def __init__(self, filename, data):
        self.filename = filename
        self.data = data
        # self.ancestry_categories = ancestry_categories
        self.writer = pd.ExcelWriter(filename, engine='xlsxwriter')

        # Order of the spreadsheets
        self.spreadsheets_list = [
            'publication', 'dataset', 'scores', 'sample_perf', 'cohorts'
        ]

        # Spreadsheets content creation
        self.spreadsheets_conf = {
            'publication': ('Publication', self.create_publication_spreadsheet),
            'dataset'    : ('Dataset', self.create_dataset_spreadsheet),
            'scores'     : ('Scores', self.create_scores_spreadsheet),
            'sample_perf': ('Performances', self.create_performance_metrics_spreadsheet),
            'cohorts'    : ('Cohorts', self.create_cohorts_spreadsheet)
        }

        # Force data type in some columns
        # 'Int64' works better than "int" because it doesn't break if a non numeric value is found (e.g. missing PMID)
        # self.spreadsheets_column_types = {
        #    'publications': { "PubMed ID (PMID)": 'Int64' },
        # }


    def save(self):
        ''' Close the Pandas Excel writer and output the Excel file '''
        self.writer.close()


    def generate_sheets(self):
    # def generate_sheets(self, csv_prefix):
        ''' Generate the differents sheets '''

        if (len(self.spreadsheets_conf.keys()) != len(self.spreadsheets_list)):
            print("Size discrepancies between the dictionary 'spreadsheets' and the list 'spreadsheets_ordering'.")
            exit()
        # if (csv_prefix == ''):
        #     print("CSV prefix, for the individual CSV spreadsheet is empty. Please, provide a prefix!")
        #     exit()

        for spreadsheet_name in self.spreadsheets_list:
            spreadsheet_label = self.spreadsheets_conf[spreadsheet_name][0]
            try:
                data = self.spreadsheets_conf[spreadsheet_name][1]()
                self.generate_sheet(data, spreadsheet_label)
                print("Spreadsheet '"+spreadsheet_label+"' done")
                # self.generate_csv(data, csv_prefix, spreadsheet_name, spreadsheet_label)
                # print("CSV '"+spreadsheet_label+"' done")
            except Exception as e:
                print(f'Issue to generate the spreadsheet "{spreadsheet_label}"\n> {e}')
                exit()


    def generate_sheet(self, data, sheet_label):
        ''' Generate the Pandas dataframe and insert it as a spreadsheet into to the Excel file '''
        try:
            # Create a Pandas dataframe.
            df = pd.DataFrame(data)
            # Convert the dataframe to an XlsxWriter Excel object.
            df.to_excel(self.writer, index=False, sheet_name=sheet_label)
        except NameError:
            print("Spreadsheet generation: At least one of the variables is not defined")
        except Exception as e:
            print(f'Spreadsheet generation: There is an issue with the data of the spreadsheet "{sheet_label}"\n> {e}')


    def generate_csv(self, data, prefix, sheet_name, sheet_label):
        ''' Generate the Pandas dataframe and create a CSV file '''
        try:
            # Create a Pandas dataframe.
            df = pd.DataFrame(data)
            # Force data type (e.g. issue with float for PubMed ID)
            if sheet_name in self.spreadsheets_column_types:
                df = df.astype(self.spreadsheets_column_types[sheet_name])
            # Convert the dataframe to an XlsxWriter Excel object.
            sheet_label = sheet_label.lower().replace(' ', '_')
            csv_filename = prefix+"_metadata_"+sheet_label+".csv"
            df.to_csv(csv_filename, index=False)
        except NameError:
            print("CSV generation: At least one of the variables is not defined")
        except Exception as e:
            print(f'CSV generation: There is an issue with the data of the type "{sheet_label}"\n> {e}')


    def generate_tarfile(self, output_filename, source_dir):
        ''' Generate a tar.gz file from a directory '''
        with tarfile.open(output_filename, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))


    def get_column_labels(self, classname, exception_field=None, exception_classname=None):
        ''' Fetch the column labels from the Models '''
        model_labels = {}
        for field in self.fields_to_include[classname]:
            field_name = field['name']
            label = field['label']
            model_labels[field_name] = label
        return model_labels


    def not_in_extra_fields_to_include(self,column:str,data:dict) -> bool:
        if column not in self.extra_fields_to_include and column in data.keys():
            return True
        else:
            return False


    def cleanup_field_value(self,value):
        ''' Remove trailing characters (including new line). '''
        if isinstance(value, str):
            value = value.strip().replace('\n',' ').replace('\t',' ')
        return value


    def create_md5_checksum(self, md5_filename='md5_checksum.txt', blocksize=4096):
        ''' Returns MD5 checksum for the generated file. '''

        md5 = hashlib.md5()
        try:
            file = open(self.filename, 'rb')
            with file:
                for block in iter(lambda: file.read(blocksize), b""):
                    md5.update(block)
        except IOError:
            print('File \'' + self.filename + '\' not found!')
            return None
        except:
            print("Error: the script couldn't generate a MD5 checksum for '" + self.filename + "'!")
            return None

        md5file = open(md5_filename, 'w')
        md5file.write(md5.hexdigest())
        md5file.close()
        print("MD5 checksum file '"+md5_filename+"' has been generated.")


    #---------------------#
    # Spreadsheet methods #
    #---------------------#

    def create_scores_spreadsheet(self):
        ''' Score spreadsheet '''

        # Fetch column labels an initialise data dictionary
        score_labels = self.get_column_labels('Score')
        scores_data = {}
        for label in list(score_labels.values()):
            scores_data[label] = []

        for score in self.data['scores']:
            for column in score_labels.keys():
                if self.not_in_extra_fields_to_include(column,score):
                    value = self.cleanup_field_value(score[column])
                    scores_data[score_labels[column]].append(value)
        return scores_data


    def create_performance_metrics_spreadsheet(self):
        ''' Performance Metrics spreadsheet '''

        # Fetch column labels an initialise data dictionary
        perf_labels = self.get_column_labels('Performance')
        perf_data = {}
        for label in list(perf_labels.values()):
            perf_data[label] = []

        for perf in self.data['performances']:
            # Load the data into the dictionnary
            for column in perf_labels.keys():
                if self.not_in_extra_fields_to_include(column,perf):
                    value = self.cleanup_field_value(perf[column])
                    perf_data[perf_labels[column]].append(value)
        return perf_data


    def create_dataset_spreadsheet(self):
        ''' Dataset spreadsheet '''

        # Fetch column labels an initialise data dictionary
        object_labels = self.get_column_labels('Dataset')
        object_data = {}
        for label in list(object_labels.values()):
            object_data[label] = []

        d_data = self.data['dataset']
        for column in object_labels.keys():
            if self.not_in_extra_fields_to_include(column,d_data):
                value = self.cleanup_field_value(d_data[column])
                object_data[object_labels[column]].append(value)
        return object_data


    def create_publication_spreadsheet(self):
        ''' Publication spreadsheet '''

        # Fetch column labels an initialise data dictionary
        object_labels = self.get_column_labels('Publication')
        object_data = {}
        for label in list(object_labels.values()):
            object_data[label] = []

        pub_data = self.data['publication']
        for column in object_labels.keys():
            if self.not_in_extra_fields_to_include(column,pub_data):
                value = self.cleanup_field_value(pub_data[column])
                object_data[object_labels[column]].append(value)
        return object_data


    def create_cohorts_spreadsheet(self):
        ''' Cohorts spreadsheet '''

        # Fetch column labels an initialise data dictionary
        object_labels = self.get_column_labels('Cohort')
        object_data = {}
        for label in list(object_labels.values()):
            object_data[label] = []

        for cohort in self.data['cohorts']:
            for column in object_labels.keys():
                if self.not_in_extra_fields_to_include(column,cohort):
                    value = self.cleanup_field_value(cohort[column])
                    object_data[object_labels[column]].append(value)
        return object_data
