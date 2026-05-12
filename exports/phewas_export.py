import os
import gzip
import csv
import shutil
import sqlite3
from omicspred.models import Dataset, Score, ScorePheWAS, Phenotype
import time

publication_id = 'OPP000005'
method_description = 'S-PrediXcan'
adjusted_pvalue_method = 'False Discovery Rate (FDR) correction applied within each score dataset–phenotype pair'
cohorts = 'MVP'


class PheWASExport:

    export_columns =  [
        {'name': 'score__id', 'label': 'omicspred_id'},
        {'name': 'score__genes__external_id', 'label': 'gene_ids', 'skip_auto_import': True},
        {'name': 'score__genes__name', 'label': 'gene_names', 'skip_auto_import': True},
        {'name': 'score__proteins__external_id', 'label': 'protein_ids', 'skip_auto_import': True},
        {'name': 'score__proteins__name', 'label': 'protein_names', 'skip_auto_import': True},
        {'name': 'score__metabolites__external_id', 'label': 'metabolite_ids', 'skip_auto_import': True},
        {'name': 'score__metabolites__name', 'label': 'metabolite_names', 'skip_auto_import': True},
        {'name': 'phenotypes__id', 'label': 'phenotype_ids', 'skip_auto_import': True},
        {'name': 'phenotypes__label', 'label': 'phenotype_labels', 'skip_auto_import': True},
        {'name': 'trait_reported', 'label': 'trait_reported'},
        {'name': 'method_description', 'label': 'method_description'},
        {'name': 'publication__id', 'label': 'phewas_publication_id'},
        {'name': 'samples__sample_number', 'label': 'sample_number', 'skip_auto_import': True},
        {'name': 'samples__sample_cases', 'label': 'sample_cases', 'skip_auto_import': True},
        {'name': 'samples__sample_controls', 'label': 'sample_controls', 'skip_auto_import': True},
        {'name': 'samples__ancestry_broad', 'label': 'ancestry', 'skip_auto_import': True},
        {'name': 'cohorts__name_short', 'label': 'cohorts', 'skip_auto_import': True},
        {'name': 'samples__source_gwas_catalog', 'label': 'gwas_catalog_id', 'skip_auto_import': True},
        {'name': 'effect_size', 'label': 'effect_size'},
        {'name': 'hr', 'label': 'HR'},
        {'name': 'hr_ci', 'label': 'HR_lower_upper'},
        {'name': 'zscore', 'label': 'z-score'},
        {'name': 'pvalue', 'label': 'p-value'},
        {'name': 'adjusted_pvalue', 'label': 'adjusted_p-value'},
        {'name': 'adjusted_pvalue_method', 'label': 'adjusted_pvalue_method'},
        # {'name': 'bonferroni', 'label': 'Bonferroni adjusted P-value'},
        {'name': 'var_gene_exp', 'label': 'var_gene_exp'},
        # {'name': 'variants_number_used', 'label': 'Number of variants used'},
        # {'name': 'variants_fraction_found', 'label': 'Fraction of variants found'}
    ]
    cols_list = [x['name'] for x in export_columns]
    nested_attr_sep = '__'

    def __init__(self, filename:str, exports_dir:str, dataset:Dataset, raw_file_dir:str=None):
        self.dataset = dataset
        self.dataset_type = dataset.omics_type
        self.filename = filename
        self.exports_dir = exports_dir
        self.filepath = f'{exports_dir}/{filename}'
        self.raw_file_dir = raw_file_dir
        self.raw_files = {}
        self.count_phewas_exported_db = 0
        if raw_file_dir:
            self.count_phewas_exported_file = 0
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
                    if attrs[1] == 'cohorts':
                        print(f'>>> {nested_model}')
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
        print("  - Get PheCode mappings")
        phecode_tmp_mappings = {}
        phecode_mappings = {}
        phenotypes = Phenotype.objects.all()
        for phenotype in phenotypes:
            phenotype_id = phenotype.id
            phenotype_label = phenotype.label
            if phenotype.traits_reported:
                for phecode in phenotype.traits_reported:
                    phecode_id = phecode['id']
                    if phecode_id not in phecode_tmp_mappings.keys():
                        phecode_tmp_mappings[phecode_id] = {}
                    phecode_tmp_mappings[phecode_id][phenotype_id] = phenotype_label
        for phecode in phecode_tmp_mappings.keys():
            phenotype_ids = ';'.join(phecode_tmp_mappings[phecode].keys())
            phenotype_labels = ';'.join(phecode_tmp_mappings[phecode].values())
            phecode_mappings[phecode] = {'ids': phenotype_ids, 'labels':phenotype_labels}
        return phecode_mappings


    def get_many_to_many(self, models:list, label:str, model_type:str, scorephewas_data:dict) -> dict:
        fields_dict = {
            'molecular_trait': { 'external_id': set(), 'name': set() },
            'phenotype': { 'id': set(), 'label': set() },
            'sample': { 'sample_number': set(), 'sample_cases': set(), 'sample_controls': set(), 'ancestry_broad': set(), 'source_gwas_catalog': set() },
            'cohort': { 'name_short': set() }
        }
        fields = fields_dict[model_type]

        if fields:
            for model in models:
                op_data = self.get_data_attr(model,fields_dict[model_type])
                for field in fields.keys():
                    if op_data[field]:
                        fields[field].add(str(op_data[field]))
            for field in fields.keys():
                scorephewas_data[f'{label}__{field}'] = ';'.join(list(fields[field]))
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
        if self.dataset_type in ['gene expression', 'protein']:
            score_phewas_data = self.get_many_to_many(score.genes.all(),'score__genes','molecular_trait',score_phewas_data)
        # Proteins
        if self.dataset_type == 'protein':
            score_phewas_data = self.get_many_to_many(score.proteins.all(),'score__proteins','molecular_trait',score_phewas_data)
        # Metabolites
        if self.dataset_type == 'metabolite':
            score_phewas_data = self.get_many_to_many(score.metabolites.all(),'score__metabolites','molecular_trait',score_phewas_data)
        ## Phenotypes ##
        score_phewas_data = self.get_many_to_many(score_phewas.phenotypes.all(),'phenotypes','phenotype',score_phewas_data)

        ## Samples ##
        samples = score_phewas.samples.all()
        score_phewas_data = self.get_many_to_many(samples,'samples','sample',score_phewas_data)
        ## Cohorts  ##
        cohorts = {}
        for sample in samples:
            for cohort in sample.cohorts.all():
                cohorts[cohort.name_short] = cohort
        score_phewas_data = self.get_many_to_many(cohorts.values(),'cohorts','cohort',score_phewas_data)
        return score_phewas_data


    def fetch_score_data_for_file(self) -> dict:
        # Fetch score data
        score_data = {}
        scores = Score.objects.filter(dataset_id=self.dataset.num).prefetch_related('genes','proteins','metabolites')
        for score in scores:
            score_id = score.id
            score_data[score_id] = {}
            # Genes
            if self.dataset_type in ['gene expression', 'protein']:
                score_genes = self.get_many_to_many(score.genes.all(),'score__genes','molecular_trait',{})
                for score_gene in score_genes.keys():
                    score_data[score_id][score_gene] = score_genes[score_gene]
            # Proteins
            if self.dataset_type == 'protein':
                score_proteins = self.get_many_to_many(score.proteins.all(),'score__proteins','molecular_trait',{})
                for score_protein in score_proteins.keys():
                    score_data[score_id][score_protein] = score_proteins[score_protein]
            # Metabolites
            if self.dataset_type == 'metabolite':
                score_metabolites = self.get_many_to_many(score.metabolites.all(),'score__metabolites','molecular_trait',{})
                for score_metabolite in score_metabolites.keys():
                    score_data[score_id][score_metabolite] = score_metabolites[score_metabolite]
        return score_data


    def get_input_file_size(self,filepath:str, type:str='mb') -> int:
        file_size_bytes = os.path.getsize(filepath)
        file_size_kb = file_size_bytes / 1024
        file_size_mb = file_size_kb / 1024
        if type == 'kb':
            return file_size_kb
        elif type == 'mb':
            return file_size_mb
        else:
            return file_size_bytes


    def set_count_prompt(self,filepath:str) -> str:
        file_size_mb = self.get_input_file_size(filepath,'mb')
        count_prompt = '000'
        if 2 <= file_size_mb < 20:
            count_prompt = '0000'
        elif 20 <= file_size_mb < 100:
            count_prompt = '00000'
        elif file_size_mb >= 100:
            count_prompt = '000000'
        return count_prompt

    def get_num_from_id(self,entry_id:str,entry_prefix:str='OPGS') -> int:
        entry_id = entry_id.upper()
        entry_num = entry_id.replace(entry_prefix, '').lstrip('0')
        return int(entry_num)


    # Generate PheWAS export from DB (i.e. significant PheWAS)
    def generate_export_from_db(self):
        t_start = time.perf_counter()
        print(f'- Get PheWAS from DB and write data')
        phewas_export_file = open(self.filepath,'w')
        # Write header
        col_headers = [x['label'] for x in self.export_columns]
        phewas_export_file.write('\t'.join(col_headers))
        rows_to_write = ''
        rows_count = 0
        prefetch_related = ['samples','phenotypes','score__genes','score__proteins','score__metabolites','samples__cohorts']
        score_phewas_list = ScorePheWAS.objects.select_related('score','publication').filter(dataset_id=self.dataset.num).prefetch_related(*prefetch_related).order_by('score_id','publication_id')
        count_block = '000' if len(score_phewas_list) < 10000 else '0000'
        for score_phewas in score_phewas_list:
            score_phewas_data = self.fetch_data(score_phewas)
            # print(f'>>> score_phewas_data: {score_phewas_data}')
            phewas_row = []
            for col in self.cols_list:
                value = score_phewas_data[col] if col in score_phewas_data.keys() else ''
                phewas_row.append(str(value))

            # Write export row in block
            rows_to_write += ('\n'+'\t'.join(phewas_row))
            rows_count += 1
            if rows_count == 250:
                phewas_export_file.write(rows_to_write)
                rows_to_write = ''
                rows_count = 0

            # phewas_export_file.write('\n'+'\t'.join(phewas_row))
            self.count_phewas_exported_db += 1
            if str(self.count_phewas_exported_db).endswith(count_block):
                print(f'  - {self.count_phewas_exported_db:,} done')
        # Write remaining rows
        if rows_count != 0:
            phewas_export_file.write(rows_to_write)
        phewas_export_file.close()
        print(f'  - {self.count_phewas_exported_db:,} done')
        print(f'  > PheWAS exported (from DB): {self.count_phewas_exported_db:,}')
        t_end = time.perf_counter()
        print(f"  >>> Execution time: {t_end - t_start:0.2f} seconds")

        # Gzip the PheWAS file
        if not self.raw_file_dir:
            with open(self.filepath, 'rb') as f_in:
                with gzip.open(f'{self.filepath}.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(self.filepath)
            print(f'  -> File zipped')


    # Generate PheWAS export from data file (i.e. all PheWAS)
    def generate_export_from_file(self) -> None:
        t_start = time.perf_counter()
        print("- Get PheWAS from file")

        phecode_mappings = self.get_phecode_mappings_from_db()
        print(f"  - Phecode mappings retrieved from DB ({len(phecode_mappings.keys()):,})")

        phewas_export_file = open(self.filepath,'a')

        rows_to_write = ''
        rows_count = 0
        count_phewas_done = 0
        count_missing_phewas_row = 0
        count_skipped = {}

        missing_phecode = set()

        dataset_id = self.dataset.id
        if dataset_id not in self.raw_files.keys():
            print(f">>> ERROR: can't find an input PheWAS file for the dataset {dataset_id} in {self.raw_file_dir}")
            exit()

        # Fetch score data
        print(f"  - Fetch Score data")
        score_data = self.fetch_score_data_for_file()
        count_file_lines = 0 # Exclude the header line
        count_mark = self.set_count_prompt(self.raw_files[dataset_id])
        count_mark_start = time.perf_counter()

        print("  - Start to read data file")
        with gzip.open(self.raw_files[dataset_id], 'rt', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                # score_start = time.perf_counter()
                count_file_lines += 1
                # Only process the non significant entries
                fdr_sig = row['fdr_sig']
                if fdr_sig != 'FALSE':
                    if fdr_sig not in count_skipped.keys():
                        count_skipped[fdr_sig] = 0
                    count_skipped[fdr_sig] += 1
                    continue

                score_phewas_data = {}
                score_id = row['OmicsPred ID']
                score_phewas_data['score__id'] = score_id
                score_phewas_data['samples__source_gwas_catalog'] = row['GWASCatalogue_accessionId']
                # Phenotypes
                phecode = row['PheCode'].replace('PheCode','').lstrip('0') # => map to Phecode => EFO dict
                phenotype_ids = ''
                phenotype_labels = ''
                if phecode in phecode_mappings.keys():
                    phenotype_ids = phecode_mappings[phecode]['ids']
                    phenotype_labels = phecode_mappings[phecode]['labels']
                else:
                    phecode_mappings_data = self.get_phecode_mappings(phecode)
                    if phecode_mappings_data:
                        efo_ids = [ x[0] for x in phecode_mappings_data ]
                        efo_labels = [ x[1] for x in phecode_mappings_data ]
                        phenotype_ids = ';'.join(efo_ids)
                        phenotype_labels = ';'.join(efo_labels)
                        phecode_mappings[phecode] = {'ids': phenotype_ids, 'labels': phenotype_labels}
                    else:
                        print(f"  >>>> Phecode {phecode}: can't find EFO mappings in OmicsPred DB nor SQLite DB")

                score_phewas_data['phenotypes__id'] = phenotype_ids
                score_phewas_data['phenotypes__label'] = phenotype_labels
                score_phewas_data['trait_reported'] = row['reportedTrait']

                # Sample data
                sample_data = row['discoverySampleAncestry'].split(' ',1) # => Split in sample_number and ancestry_broad
                score_phewas_data['samples__sample_number'] = sample_data[0]
                score_phewas_data['samples__ancestry_broad'] = sample_data[1]

                score_phewas_data['zscore'] = row['zscore']
                score_phewas_data['pvalue'] = row['pvalue']
                score_phewas_data['adjusted_pvalue'] = row['fdr']
                score_phewas_data['adjusted_pvalue_method'] = adjusted_pvalue_method
                score_phewas_data['effect_size'] = row['effect_size']
                score_phewas_data['var_gene_exp'] = row['var_g']

                # Add: publication_id, method_description
                score_phewas_data['publication__id'] = publication_id
                score_phewas_data['method_description'] = method_description

                # Populate score_phewas_data with the linked molecular trait(s)
                for mt_data_key in score_data[score_id].keys():
                    score_phewas_data[mt_data_key] = score_data[score_id][mt_data_key]

                # Add: null data for missing values
                empty_cols = ['samples__sample_cases','samples__sample_controls','hr','hr_ci']
                for empty_col in empty_cols:
                    score_phewas_data[empty_col] = ''

                phewas_row = []
                for col in self.cols_list:
                    value = score_phewas_data[col] if col in score_phewas_data.keys() else ''
                    phewas_row.append(str(value))
                del score_phewas_data

                if phewas_row:
                    # Write export row in block
                    rows_to_write += ('\n'+'\t'.join(phewas_row))
                    rows_count += 1
                    if rows_count == 250:
                        phewas_export_file.write(rows_to_write)
                        rows_to_write = ''
                        rows_count = 0
                    self.count_phewas_exported_file += 1
                    count_phewas_done += 1
                else:
                    count_missing_phewas_row += 1
                del phewas_row

                # score_end = time.perf_counter()
                # score_time = score_end-score_start
                # if score_time > 0:
                #     print(f'    >>> Score executed: {score_time} seconds')
                if str(count_phewas_done).endswith(count_mark):
                    count_mark_end = time.perf_counter()
                    print(f'    - {count_phewas_done:,} done ({count_mark_end - count_mark_start:0.2f} seconds)')
                    count_mark_start = count_mark_end
        count_mark_end = time.perf_counter()
        print(f'    - {count_phewas_done:,} done ({count_mark_end - count_mark_start:0.2f} seconds)')
        # Write remaining rows
        if rows_count != 0:
            phewas_export_file.write(rows_to_write)
        phewas_export_file.close()
        # Exported rows
        print(f'  > PheWAS exported (from file): {self.count_phewas_exported_file:,}')
        print(f'    + Skipped rows: {count_skipped}')
        print(f'    + Missing phewas rows: {count_missing_phewas_row}')
        # print(f"  - Phecode mappings retrieved from DB - end ({len(phecode_mappings.keys()):,})")
        if missing_phecode:
            print('# Missing PheCodes:')
            print(sorted(missing_phecode))

        # Total row counts
        total_lines_exported = self.count_phewas_exported_db + self.count_phewas_exported_file
        print(f'# Total PheWAS exported : {total_lines_exported:,}')

        # Total execution time
        t_end = time.perf_counter()
        print(f"  >>> Execution time: {t_end - t_start:0.2f} seconds")

        # Gzip file
        new_name = self.filepath.replace('.txt','_all.txt')
        os.rename(self.filepath,new_name)
        with open(new_name, 'rb') as f_in:
            with gzip.open(f'{new_name}.gz', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.remove(new_name)
            print(f'  -> File zipped')

        # Check number of rows
        if total_lines_exported != count_file_lines:
            print(f'!!!! Number of lines is different between the input file ({count_file_lines:,}) and the exported file ({total_lines_exported:,})')
            exit()


    def generate_export(self):
        self.generate_export_from_db()
        if self.raw_file_dir:
            self.generate_export_from_file()

    