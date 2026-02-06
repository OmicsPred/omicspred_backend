import os
import gzip
import csv
import sqlite3
from omicspred.models import *
from exports.config import sqlite_default_values


class SqliteExport:

    # Flag for GTEx studies
    gtex_prefix_study = 'GTExV8'
    # For GTEx studies
    tissues_mapping = {
        "subcutaneous adipose tissue": "Adipose_Subcutaneous",
        "omental fat pad": "Adipose_Visceral_Omentum",
        "adrenal gland": "Adrenal_Gland",
        "ascending aorta": "Artery_Aorta",
        "coronary artery": "Artery_Coronary",
        "tibial artery": "Artery_Tibial",
        "amygdala": "Brain_Amygdala",
        "anterior cingulate cortex": "Brain_Anterior_cingulate_cortex_BA24",
        "caudate nucleus": "Brain_Caudate_basal_ganglia",
        "cerebellar hemisphere": "Brain_Cerebellar_Hemisphere",
        "cerebellum": "Brain_Cerebellum",
        "frontal cortex": "Brain_Cortex",
        "dorsolateral prefrontal cortex": "Brain_Frontal_Cortex_BA9",
        "Ammon's horn": "Brain_Hippocampus",
        "hypothalamus": "Brain_Hypothalamus",
        "nucleus accumbens": "Brain_Nucleus_accumbens_basal_ganglia",
        "putamen": "Brain_Putamen_basal_ganglia",
        "C1 segment of cervical spinal cord": "Brain_Spinal_cord_cervical_c-1",
        "substantia nigra": "Brain_Substantia_nigra",
        "breast epithelium": "Breast_Mammary_Tissue",
        "fibroblast derived cell line": "Cells_Cultured_fibroblasts",
        "lymphoblast": "Cells_EBV-transformed_lymphocytes",
        "sigmoid colon": "Colon_Sigmoid",
        "transverse colon": "Colon_Transverse",
        "gastroesophageal sphincter": "Esophagus_Gastroesophageal_Junction",
        "esophagus squamous epithelium": "Esophagus_Mucosa",
        "esophagus muscularis mucosa": "Esophagus_Muscularis",
        "right atrium auricular region": "Heart_Atrial_Appendage",
        "left ventricle myocardium": "Heart_Left_Ventricle",
        "cortex of kidney": "Kidney_Cortex",
        "right lobe of liver": "Liver",
        "upper lobe of left lung": "Lung",
        "anterior lingual gland": "Minor_Salivary_Gland",
        "gastrocnemius medialis": "Muscle_Skeletal",
        "tibial nerve": "Nerve_Tibial",
        "ovary": "Ovary",
        "body of pancreas": "Pancreas",
        "pituitary gland": "Pituitary",
        "prostate gland": "Prostate",
        "suprapubic skin": "Skin_Not_Sun_Exposed_Suprapubic",
        "lower leg skin": "Skin_Sun_Exposed_Lower_leg",
        "Peyer's patch": "Small_Intestine_Terminal_Ileum",
        "spleen": "Spleen",
        "stomach": "Stomach",
        "testis": "Testis",
        "thyroid gland": "Thyroid",
        "uterus": "Uterus",
        "vagina": "Vagina",
        "venous blood": "Whole_Blood"
    }
    methods_mapping = {
        'Enet': 'Elastic Net',
        'MASHR': 'MASHR'
    }
    platforms_mapping = {
        'eQTL': 'RNAseq - Expression',
        'sQTL': 'RNAseq - Splicing'
    }


    def __init__(self, opp_id:str, sqlite_dir:str, scoring_files_dir:str, datasets: list, use_opgs_id_as_gene:bool, insert_block_max:int=100):
        self.opp_id = opp_id
        self.sqlite_dir = sqlite_dir
        self.scoring_files_dir = scoring_files_dir
        self.datasets = datasets # List of Dataset models
        self.use_opgs_id_as_gene = use_opgs_id_as_gene
        self.insert_block_max = insert_block_max


    def read_scoring_file(self, dataset_dir:str, score_id:str, dataset_name:str, reported_trait_id:str, molecular_traits:dict, genome_build:str) -> list:
        ''' Read content of the scoring file '''
        scoring_file = f'{self.scoring_files_dir}/{dataset_dir}/{score_id}.txt'
        scoring_file_gz = f'{self.scoring_files_dir}/{dataset_dir}/{score_id}.txt.gz'
        data = []
        if not os.path.isfile(scoring_file):
            scoring_file = f'{self.scoring_files_dir}/{dataset_dir}/{score_id}_model.txt'

        # Text file
        if os.path.isfile(scoring_file):
            with open(scoring_file, newline='') as sc_file:
                # Ignore lines starting with '#'
                reader = csv.DictReader(filter(lambda row: row[0]!='#', sc_file), delimiter='\t')
                for row in reader:
                    variant_info = self.get_variant_info(row,score_id,dataset_name,reported_trait_id,molecular_traits,genome_build)
                    data.append(variant_info)
        # Zipped file
        elif os.path.isfile(scoring_file_gz):
            with gzip.open(scoring_file_gz, mode="rt") as sc_file:
                # Ignore lines starting with '#'
                reader = csv.DictReader(filter(lambda row: row[0]!='#', sc_file), delimiter='\t')
                for row in reader:
                    variant_info = self.get_variant_info(row,score_id,dataset_name,reported_trait_id,molecular_traits,genome_build)
                    data.append(variant_info)
        else:
            print(f">>> ERROR: file not found ({scoring_file} nor {scoring_file_gz}")
        return data


    def get_variant_info(self, row:dict, score_id:str, dataset_name:str, reported_trait_id:str, molecular_traits:dict, genome_build:str) -> tuple:
        ''' Fetch variant information of a row in the scoring file '''
        rsid = row['rsID'] if 'rsID' in row.keys() else row['rsid']
        varid = None
        if 'chr_name' in row.keys() and 'chr_position' in row.keys():
            # 1_156000340_A_G_b38
            to_replace = 'GRCh' if genome_build.startswith('GRCh') else 'hg'
            build = 'b'+genome_build.replace(to_replace,'')
            varid = f"{row['chr_name']}_{row['chr_position']}_{row['other_allele']}_{row['effect_allele']}_{build}"
        elif 'variant_description' in row.keys():
            if row['variant_description'].startswith('variant_id=chr'):
                varid = row['variant_description'].split('=')[1]
        gene_id = molecular_traits['gene_id']
        if self.gtex_prefix_study in dataset_name:
            variant_info_list = [
                score_id,             # omicspred_id
                reported_trait_id,    # gene
            ]
        else:
            variant_info_list = [
                score_id,             # omicspred_id
                gene_id,              # gene
            ]
        if 'protein_id' in molecular_traits.keys():
            variant_info_list.append(molecular_traits['protein_id']) # protein    
        
        variant_info_list.extend([
            rsid,                 # rsid
            varid,                # var_id
            row['other_allele'],  # ref_allele
            row['effect_allele'], # eff_allele
            row['effect_weight']  # weight
        ])
        return tuple(variant_info_list)
    

    def create_table_extra(self, cur:sqlite3.Cursor, is_proteomics:bool) -> list:
        if self.use_opgs_id_as_gene:
            cols_extra = ['gene', 'gene_id', 'genename', 'gene_type']
        else:
            cols_extra = ['omicspred_id', 'gene', 'genename', 'gene_type']
        if is_proteomics:
            cols_extra.append('protein')
        cols_extra.extend(['"n.snps.in.model"', 'cv_R2_avg', '"pred.perf.R2"', 'nested_cv_fisher_pval', 'rho_avg', '"pred.perf.pval"', '"pred.perf.qval"'])
        cur.execute("DROP TABLE IF EXISTS extra;")
        cur.execute(f"CREATE TABLE extra({', '.join(cols_extra)})")
        return cols_extra


    def create_table_weights(self, cur:sqlite3.Cursor, is_proteomics:bool) -> None:
        if self.use_opgs_id_as_gene:
            cols_weights = ['gene', 'gene_id']
        else:
            cols_weights = ['omicspred_id', 'gene']
        if is_proteomics:
            cols_weights.append('protein')
        cols_weights.extend(['rsid', 'varID', 'ref_allele', 'eff_allele','weight'])
        cur.execute("DROP TABLE IF EXISTS weights;")
        cur.execute(f"CREATE TABLE weights({', '.join(cols_weights)})") 


    def create_other_tables(self, cur:sqlite3.Cursor) -> None:
        # Table 'sample_info'
        cur.execute("DROP TABLE IF EXISTS sample_info;")
        cur.execute(f'CREATE TABLE sample_info("n.samples")')

        # Table 'genome_build'
        cur.execute("DROP TABLE IF EXISTS genome_build;")
        cur.execute(f'CREATE TABLE genome_build("build")')

    def insert_training_samples(self, cur:sqlite3.Cursor, con:sqlite3.Connection, dataset:Dataset) -> None:
        # Training samples
        sample_count = 0
        for sample_training in dataset.samples_training.all():
            sample_count += sample_training.sample_number
        if sample_count != 0:
            cur.execute("INSERT INTO sample_info VALUES (?)", (sample_count,))
            con.commit()

    def get_metrics(self,score:Score) -> dict:
        metrics = {}
        for perf in score.score_performance.all():
            if perf.eval_type == 'Training' or perf.eval_type == 'T':
                for metric in perf.performance_metric.all():
                    if metric.name_short == 'R2':
                        metrics['R2'] = metric.estimate
                        metrics['R2_pval'] = metric.pvalue
                    elif metric.name_short == 'Rho':
                        metrics['Rho'] = metric.estimate
                        metrics['Rho_pval'] = metric.pvalue
        return metrics


    def get_score_data(self, dataset_name:str, score:Score, gene:Gene, reported_trait_id:str, gene_id:str, is_proteomics:bool, metrics:dict) -> dict:
        score_id = score.id
        if self.gtex_prefix_study in dataset_name:
            score_data = {
                'omicspred_id': score_id,
                'gene': reported_trait_id,
                'genename': gene.name,
                'gene_type': gene.biotype
            }
        else:
            if self.use_opgs_id_as_gene:
                score_data = {
                    'gene': score_id,
                    'gene_id': gene_id,
                    'genename': gene.name,
                    'gene_type': gene.biotype
                }
            else:
                score_data = {
                    'omicspred_id': score_id,
                    'gene': gene_id,
                    'genename': gene.name,
                    'gene_type': gene.biotype
                }
        if is_proteomics:
            proteins = score.proteins.all()
            protein = proteins[0]
            score_data['protein'] = protein.external_id
        metrics_keys = metrics
        score_data['"n.snps.in.model"'] = score.variants_number
        score_data['cv_R2_avg'] = metrics['R2'] if 'R2' in metrics_keys else None
        score_data['"pred.perf.R2"'] = None
        score_data['nested_cv_fisher_pval'] = metrics['R2_pval'] if 'R2_pval' in metrics_keys else None
        score_data['rho_avg'] = metrics['Rho'] if 'Rho' in metrics_keys else None
        score_data['"pred.perf.pval"'] = metrics['Rho_pval'] if 'Rho_pval' in metrics_keys else None
        score_data['"pred.perf.qval"'] = None
        return score_data


    def generate_sqlite_files(self):
        ds_count = 1
        ds_total_count = len(self.datasets)
        for dataset in self.datasets:
            print(f"- Dataset: {dataset.id} ({ds_count}/{ds_total_count})")
            genome_build = ''
            ds_count += 1
            dataset_name = dataset.name
            dataset_type = dataset.platform.platform_master.type
            is_proteomics = True if dataset_type == 'Proteomics' else False
            dataset_label = dataset_name
            if self.gtex_prefix_study in dataset_name:
                ds_components = dataset_name.split(' - ')
                dataset_label = f'{ds_components[0]}_{ds_components[3]}_{ds_components[1]}_{ds_components[2]}'
                method_name = self.methods_mapping[ds_components[2]]
                platform_name = self.platforms_mapping[ds_components[1]]
                if method_name != sqlite_default_values['method_name'] or platform_name != sqlite_default_values['platform_name']:
                    print('\t> Skipped')
                    continue
            dataset_label = dataset_label.replace(' ','_').replace("'",'_')
            sql_file = f'{dataset.id}_{dataset_label}.db'
            # print(f'dataset_name: {dataset_name}')
            # print(f'label: {dataset_label}')
            print(f"\t-> SQLite: {sql_file}")
            
            ## Create database
            con = sqlite3.connect(f'{self.sqlite_dir}/{sql_file}')
            cur = con.cursor()

            ## Create tables
            # Table 'extra'
            cols_extra = self.create_table_extra(cur,is_proteomics)

            # Table 'weights'
            self.create_table_weights(cur,is_proteomics)

            # Table 'sample_info' and 'genome_build'
            self.create_other_tables(cur)

            # For GTEx datasets
            dataset_tissue = dataset.tissue.label
            if dataset_tissue in self.tissues_mapping.keys():
                dataset_dir = self.tissues_mapping[dataset_tissue]
            else:
                dataset_dir = dataset.id
            
            insert_extra_block = []
            insert_weights_block = []

            # Training samples
            self.insert_training_samples(cur,con,dataset)

            extra_values_list = [ '?' for x in cols_extra]
            extra_values = ', '.join(extra_values_list)

            # For each score
            scores = Score.objects.filter(dataset=dataset).order_by('num')
            for score in scores:
                score_id = score.id
                genes = score.genes.all()
                gene = genes[0]
                gene_id = gene.external_id
                reported_trait_id = score.trait_reported_id
                if self.gtex_prefix_study in dataset_name and score.name.startswith('intron_'):
                    intron_name = score.name.split('_')
                    reported_trait_id = f'{intron_name[0]}_{intron_name[1]}_{intron_name[2]}_{intron_name[3]}'
                # Get performance metrics (Training)
                metrics = self.get_metrics(score)

                # Genome build
                if genome_build == '':
                    genome_build = score.variants_genomebuild

                # 1 - Extract metadata data from DB + insert data in SQLite
                score_data = self.get_score_data(dataset_name,score,gene,reported_trait_id,gene_id, is_proteomics, metrics)
                data_list = []
                for col in cols_extra:
                    data_list.append(score_data[col])
                data2insert = tuple(data_list)
                insert_extra_block.append(data2insert)

                if len(insert_extra_block) == self.insert_block_max:
                    cur.executemany(f"INSERT INTO extra VALUES({extra_values})", insert_extra_block)
                    con.commit()
                    insert_extra_block = []

                # 2 - Extract data from scoring file + insert data in SQLite
                molecular_traits = {'gene_id': gene_id}
                weights_values = '?, ?, ?, ?, ?, ?, ?'
                if is_proteomics:
                    molecular_traits['protein_id'] = score_data['protein']
                    weights_values += ', ?'
                insert_weights_block = self.read_scoring_file(dataset_dir,score_id,dataset_name,reported_trait_id,molecular_traits,genome_build)
            
                cur.executemany(f"INSERT INTO weights VALUES({weights_values})", insert_weights_block)
                con.commit()

            # TODO: place in function to avoid code duplication
            if len(insert_extra_block) != 0:
                cur.executemany(f"INSERT INTO extra VALUES({extra_values})", insert_extra_block)
                con.commit()
                insert_extra_block = []

            # Add genome build information
            if genome_build == '':
                genome_build = 'NA'
            cur.execute("INSERT INTO genome_build VALUES (?)", (genome_build,))
            con.commit()

            ## FOR test - begin ##
            # con.close()
            # exit()
            ## FOR test - end ####

        con.close()