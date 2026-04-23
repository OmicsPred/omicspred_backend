import os
import gzip
import csv
import shutil
import sqlite3
from omicspred.models import Dataset, Score, ScorePheWAS, Phenotype


publication_id = 5
method_description = 'S-PrediXcan'

class PheWASExport:

    export_columns =  [
        {'name': 'score__id', 'label': 'OmicsPred ID'},
        {'name': 'score__genes__external_id', 'label': 'Gene ID(s)', 'skip_auto_import': True},
        {'name': 'score__genes__name', 'label': 'Gene name(s)', 'skip_auto_import': True},
        {'name': 'score__proteins__external_id', 'label': 'Protein ID(s)', 'skip_auto_import': True},
        {'name': 'score__proteins__name', 'label': 'Protein name(s)', 'skip_auto_import': True},
        {'name': 'score__metabolites__external_id', 'label': 'Metabolite ID(s)', 'skip_auto_import': True},
        {'name': 'score__metabolites__name', 'label': 'Metabolite name(s)', 'skip_auto_import': True},
        {'name': 'phenotypes__id', 'label': 'Phenotype ID(s)', 'skip_auto_import': True},
        {'name': 'phenotypes__label', 'label': 'Phenotype name(s)', 'skip_auto_import': True},
        {'name': 'trait_reported', 'label': 'Reported Trait'},
        {'name': 'method_description', 'label': 'Method Description'},
        {'name': 'publication__id', 'label': 'Publication ID'},
        {'name': 'samples__sample_number', 'label': 'Sample participants', 'skip_auto_import': True},
        {'name': 'samples__sample_cases', 'label': 'Sample cases', 'skip_auto_import': True},
        {'name': 'samples__sample_controls', 'label': 'Sample controls', 'skip_auto_import': True},
        {'name': 'samples__ancestry_broad', 'label': 'Ancestry(ies)', 'skip_auto_import': True},
        {'name': 'samples__source_gwas_catalog', 'label': 'GWAS Catalog ID', 'skip_auto_import': True},
        {'name': 'effect_size', 'label': 'Effect size'},
        {'name': 'hr', 'label': 'HR / OR'},
        {'name': 'hr_ci', 'label': 'HR / OR CI'},
        {'name': 'pvalue', 'label': 'P-value'},
        {'name': 'fdr', 'label': 'Adjusted P-value'},
        {'name': 'zscore', 'label': 'Z-score'},
        # {'name': 'bonferroni', 'label': 'Bonferroni adjusted P-value'},
        {'name': 'var_gene_exp', 'label': 'Variance of the gene expression'},
        # {'name': 'variants_number_used', 'label': 'Number of variants used'},
        # {'name': 'variants_fraction_found', 'label': 'Fraction of variants found'}
    ]
    cols_list = [x['name'] for x in export_columns]
    nested_attr_sep = '__'

    def __init__(self, filename:str, exports_dir:str, dataset:Dataset, raw_file_dir:str=None):
        self.dataset = dataset
        self.filename = filename
        self.exports_dir = exports_dir
        self.filepath = f'{exports_dir}/{filename}'
        self.phewas_exported = set()
        self.raw_file_dir = raw_file_dir
        self.raw_files = {}
        if raw_file_dir:
            self.phecode_mapping_sqlite_filepath = f'{raw_file_dir}/metadata/phecode.db'
            for file in os.listdir(raw_file_dir):
                if file.startswith('OPD') and file.endswith('.csv.gz'):
                    files_parts = file.split('_')
                    self.raw_files[files_parts[0]] = f'{raw_file_dir}/{file}'


    def get_data_attr(self, model:object, fields_list:list=[])-> dict:
        export_data = {}
        if fields_list:
            for field_name in fields_list:
                value = getattr(model, field_name)
                export_data[field_name] = self.cleanup_values(value)
        else:
            for field in self.export_columns:
                # Skip the ManyToMany relations and the non native fields
                if 'skip_auto_import' in field.keys():
                    continue
                field_name = field['name']
                if self.nested_attr_sep in field_name:
                    attrs = field_name.split(self.nested_attr_sep)
                    nested_model = getattr(model,attrs[0])
                    value = getattr(nested_model,attrs[1])
                    export_data[field_name] = self.cleanup_values(value)
                else:
                    value = getattr(model, field_name)
                    export_data[field_name] = self.cleanup_values(value)
        return export_data


    def cleanup_values(self,value:str|int|float):
        value = str(value)
        if value == None or value == 'None':
             value = ''
        elif value == '1.0':
            value = '1'
        return value
    

    def get_phecode_mappings_from_db(self):
        print("- Get PheCode mappings")
        phecode_mappings = {}
        phenotypes = Phenotype.objects.all()
        for phenotype in phenotypes:
            phenotype_id = phenotype.id
            phenotype_label = phenotype.label
            if phenotype.traits_reported:
                for phecode in phenotype.traits_reported:
                    phecode_id = phecode['id']
                    if phecode_id not in phecode_mappings.keys():
                        phecode_mappings[phecode_id] = {}
                    phecode_mappings[phecode_id][phenotype_id] = phenotype_label
        return phecode_mappings


    def get_many_to_many(self, models:list, label:str, model_type:str, scorephewas_data:dict) -> dict:
        fields_dict = {
            'molecular_trait': { 'external_id': [], 'name': [] },
            'phenotype': { 'id': [], 'label': [] },
            'sample': {'sample_number': [], 'sample_cases': [], 'sample_controls': [], 'ancestry_broad': [], 'source_gwas_catalog': [] }
        }
        fields = fields_dict[model_type]

        if fields:
            for model in models:
                op_data = self.get_data_attr(model,fields_dict[model_type])
                for field in fields.keys():
                    if op_data[field]:
                        fields[field].append(str(op_data[field]))
            for field in fields.keys():   
                scorephewas_data[f'{label}__{field}'] = ';'.join(fields[field])
        return scorephewas_data
    

    def get_phecode_mappings(self, phecode_id:str):
        con = sqlite3.connect(self.phecode_mapping_sqlite_filepath)
        cur = con.cursor()
        cur.execute('SELECT distinct efo_id,efo_label FROM phecode WHERE phecode_id=?', (phecode_id,))
        phecode_data = cur.fetchall()
        cur.close()
        con.close()
        return phecode_data


    def fetch_data(self, score_phewas:ScorePheWAS):
        # Main PheWAS data (simplest to fetch)
        score_phewas_data = self.get_data_attr(score_phewas)
        ## Molecular Traits ##
        score = score_phewas.score
        # Genes
        score_phewas_data = self.get_many_to_many(score.genes.all(),'score__genes','molecular_trait',score_phewas_data)
        # Proteins
        score_phewas_data = self.get_many_to_many(score.proteins.all(),'score__proteins','molecular_trait',score_phewas_data)
        # Metabolites
        score_phewas_data = self.get_many_to_many(score.metabolites.all(),'score__metabolites','molecular_trait',score_phewas_data)
        ## Phenotypes ##
        score_phewas_data = self.get_many_to_many(score_phewas.phenotypes.all(),'phenotypes','phenotype',score_phewas_data)

        ## Samples ##
        score_phewas_data = self.get_many_to_many(score_phewas.samples.all(),'samples','sample',score_phewas_data)
        return score_phewas_data


    # Generate PheWAS export from DB (i.e. significant PheWAS)
    def generate_export_from_db(self):
        print(f'- Get PheWAS from DB and write data')
        phewas_export_file = open(self.filepath,'w')
        count_phewas_done = 0
        # Write header
        col_headers = [x['label'] for x in self.export_columns]
        phewas_export_file.write('\t'.join(col_headers))
        rows_to_write = ''
        rows_count = 0
        score_phewas_list = ScorePheWAS.objects.filter(dataset_id=self.dataset.num).order_by('score_id','publication_id')
        for score_phewas in score_phewas_list:
            score_phewas_data = self.fetch_data(score_phewas)
            # print(f'>>> score_phewas_data: {score_phewas_data}')
            phewas_row = []
            for col in self.cols_list:
                value = score_phewas_data[col] if col in score_phewas_data.keys() else ''
                phewas_row.append(str(value))

            # TMP row ID
            phewas_score_id = score_phewas_data['score__id']
            phewas_gcst_id = score_phewas_data['samples__source_gwas_catalog']
            phewas_fdr = score_phewas_data['fdr']
            # Keep track of the PheWAS already exported (when exporting all the data)
            if self.raw_file_dir:
                phewas_tmp_id = f'{phewas_score_id}_{phewas_gcst_id}_{phewas_fdr}'
                self.phewas_exported.add(phewas_tmp_id)
            # Write export row in block
            rows_to_write += ('\n'+'\t'.join(phewas_row))
            rows_count += 1
            if rows_count == 50:
                phewas_export_file.write(rows_to_write)
                rows_to_write = ''
                rows_count = 0

            # phewas_export_file.write('\n'+'\t'.join(phewas_row))
            count_phewas_done += 1
            if str(count_phewas_done).endswith('000'):
                print(f'  - {count_phewas_done} done')
        # Write remaining rows
        if rows_count != 0:
            phewas_export_file.write(rows_to_write)
        phewas_export_file.close()

        # Gzip the PheWAS file
        if not self.raw_file_dir:
            with open(self.filepath, 'rb') as f_in:
                with gzip.open(f'{self.filepath}.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(self.filepath)
            print(f'  -> File zipped')


    def generate_export_from_file(self):

        phecode_mappings = self.get_phecode_mappings_from_db()

        phewas_export_file = open(self.filepath,'a')
        
        count_phewas_done = 0
        count_phewas_exported = 0

        missing_phecode = set()
       
        print("- Get PheWAS from file")
        dataset_id = self.dataset.id
        if dataset_id not in self.raw_files.keys():
            print(f">>> ERROR: can't find an input PheWAS file for the dataset {dataset_id} in {self.raw_file_dir}")
            exit()
        
        with gzip.open(self.raw_files[dataset_id], 'rt', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                score_phewas_data = {}
                score_id = row['OmicsPred ID']
                score_phewas_data['score__id'] = score_id
                score_phewas_data['samples__source_gwas_catalog'] = row['GWASCatalogue_accessionId']
                # Phenotypes
                phecode = row['PheCode'].replace('PheCode','') # => map to Phecode => EFO dict
                phenotype_ids = ''
                phenotype_labels = ''
                if phecode in phecode_mappings.keys():
                    phenotype_ids = ';'.join(phecode_mappings[phecode].keys())
                    phenotype_labels = ';'.join(phecode_mappings[phecode].values())
                else:
                    phecode_mappings_data = self.get_phecode_mappings(phecode)
                    if phecode_mappings_data:
                        efo_ids = [ x[0] for x in phecode_mappings_data ]
                        efo_labels = [ x[1] for x in phecode_mappings_data ]
                        phenotype_ids = ';'.join(efo_ids)
                        phenotype_labels = ';'.join(efo_labels)
                    else:
                        print(f"  >>>> Phecode {phecode}: can't find EFO mappings in OmicsPred DB nor SQLite DB")

                    # print(f"  >>>> Phecode {phecode}: can't find EFO mappings in DB")
                score_phewas_data['phenotypes__id'] = phenotype_ids
                score_phewas_data['phenotypes__label'] = phenotype_labels
                score_phewas_data['trait_reported'] = row['reportedTrait']

                sample_data = row['discoverySampleAncestry'].split(' ',1) # => Split in sample_number and ancestry_broad
                score_phewas_data['samples__sample_number'] = sample_data[0]
                score_phewas_data['samples__ancestry_broad'] = sample_data[1]
                score_phewas_data['zscore'] = row['zscore']
                score_phewas_data['pvalue'] = row['pvalue']
                score_phewas_data['fdr'] = row['fdr']
                score_phewas_data['effect_size'] = row['effect_size']
                score_phewas_data['var_gene_exp'] = row['var_g']
                # Add: publication_id, method_description
                # Add: score genes/proteins/metabolites
                try:
                    score = Score.objects.get(id__iexact=score_id)
                    score_phewas_data = self.get_many_to_many(score.genes.all(),'score__genes','molecular_trait',score_phewas_data)
                    # Proteins
                    score_phewas_data = self.get_many_to_many(score.proteins.all(),'score__proteins','molecular_trait',score_phewas_data)
                    # Metabolites
                    score_phewas_data = self.get_many_to_many(score.metabolites.all(),'score__metabolites','molecular_trait',score_phewas_data)
                except Score.DoesNotExist:
                    print(f"  >> ERROR: can't find {score_id} in DB")
                    exit()

                # Add: null data for missing values
                empty_cols = ['samples__sample_cases','samples__sample_controls','hr','hr_ci']
                for empty_col in empty_cols:
                    score_phewas_data[empty_col] = ''

                phewas_row = []
                for col in self.cols_list:
                    value = score_phewas_data[col] if col in score_phewas_data.keys() else ''
                    phewas_row.append(str(value))

                # TMP row ID
                phewas_score_id = score_phewas_data['score__id']
                phewas_gcst_id = score_phewas_data['samples__source_gwas_catalog']
                phewas_fdr = score_phewas_data['fdr']
                phewas_tmp_id = f'{phewas_score_id}_{phewas_gcst_id}_{phewas_fdr}'
                if phewas_tmp_id not in self.phewas_exported:
                    # Write export row
                    phewas_export_file.write('\n'+'\t'.join(phewas_row))
                    count_phewas_exported += 1
                count_phewas_done += 1
                if str(count_phewas_done).endswith('000'):
                    print(f'  - {count_phewas_done} done')
            print(f'- PheWAS exported: {count_phewas_exported}')
            print('# Missing PheCodes:')
            print(sorted(missing_phecode))

    def generate_export(self):
        self.generate_export_from_db()
        if self.raw_file_dir:
            self.generate_export_from_file()

    