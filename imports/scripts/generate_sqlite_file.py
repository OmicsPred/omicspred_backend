import os
import gzip
import csv
import sqlite3
from omicspred.models import *


insert_block_max = 100

default_values = {
    'opp_id': 'OPP000003',
    'sqlite_dir': '/Users/lg10/Workspace/datafiles/OmicsPred/GTEx_V8/sqlite_exports',
    'scoring_files_dir': '/Users/lg10/Workspace/datafiles/OmicsPred/GTEx_V8/genetic_scores_gzip'
}

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


def read_scoring_file(scoring_files_dir:str, dataset_dir:str, score_id:str, molecular_traits:dict) -> list:
    scoring_file = f'{scoring_files_dir}/{dataset_dir}/{score_id}.txt'
    scoring_file_gz = f'{scoring_files_dir}/{dataset_dir}/{score_id}.txt.gz'
    data = []
    if not os.path.isfile(scoring_file):
        scoring_file = f'{scoring_files_dir}/{dataset_dir}/{score_id}_model.txt'

    # Text file
    if os.path.isfile(scoring_file):
        with open(scoring_file, newline='') as sc_file:
            # Ignore lines starting with '#'
            reader = csv.DictReader(filter(lambda row: row[0]!='#', sc_file), delimiter='\t')
            for row in reader:
                variant_info = get_variant_info(row,score_id,molecular_traits)
                data.append(variant_info)
    # Zipped file
    elif os.path.isfile(scoring_file_gz):
        with gzip.open(scoring_file_gz, mode="rt") as sc_file:
            # Ignore lines starting with '#'
            reader = csv.DictReader(filter(lambda row: row[0]!='#', sc_file), delimiter='\t')
            for row in reader:
                variant_info = get_variant_info(row,score_id,molecular_traits)
                data.append(variant_info)
    else:
        print(f">>> ERROR: file not found ({scoring_file} nor {scoring_file_gz}")
    return data


def get_variant_info(row:dict, score_id:str, molecular_traits:dict) -> tuple:
    rsid = row['rsID'] if 'rsID' in row.keys() else row['rsid']
    # TODO - 1: generate varID =>
    # => fetch chr_name and chr_position if they exist in the file
    # => otherwise use Ensembl REST API to fetch coordinates 
    gene_id = molecular_traits['gene_id']
    variant_info_list = [
        score_id,             # omicspred_id
        gene_id,              # gene
    ]
    if 'protein_id' in molecular_traits.keys():
        variant_info_list.append(molecular_traits['protein_id']) # protein    
    
    variant_info_list.extend([
        rsid,                 # rsid
        None,                 # var_id
        row['other_allele'],  # ref_allele
        row['effect_allele'], # eff_allele
        row['effect_weight']  # weight
    ])
    return tuple(variant_info_list)


def run(*args):

    if args:
        opp_id = args[0]
        sqlite_dir = args[1]
        scoring_files_dir = args[2]
    else:
        opp_id = default_values['opp_id']
        sqlite_dir = default_values['sqlite_dir']
        scoring_files_dir = default_values['scoring_files_dir']

    # 1 - Loop dataset (via DB or dictionary)
    datasets = Dataset.objects.filter(publication__id=opp_id).order_by('id')

    # Name, e.g. OPD000009_GTExV8_omental_fat_pad.db
    ds_count = 1
    ds_total_count = len(datasets)
    for dataset in datasets:
        print(f"- Dataset: {dataset.id} ({ds_count}/{ds_total_count})")
        ds_count += 1
        dataset_name = dataset.name
        dataset_type = dataset.platform.platform_master.type
        is_proteomics = True if dataset_type == 'Proteomics' else False
        dataset_label = dataset_name.replace(' ','_').replace("'",'_')
        sql_file = f'{dataset.id}_{dataset_label}.db'
        print(f"\t-> SQLite: {sql_file}")
        
        ## Create database
        con = sqlite3.connect(f'{sqlite_dir}/{sql_file}')
        cur = con.cursor()
        ## Create tables
        # Table 'extra'
        cols_extra = ['omicspred_id', 'gene', 'genename', 'gene_type']
        if is_proteomics:
            cols_extra.append('protein')
        cols_extra.extend(['"n.snps.in.model"', 'cv_R2_avg', 'nested_cv_fisher_pval', 'rho_avg', '"pred.perf.pval"'])
        cur.execute("DROP TABLE IF EXISTS extra;")
        cur.execute(f"CREATE TABLE extra({', '.join(cols_extra)})")

        # Table 'weights'
        cols_weights = ['omicspred_id', 'gene']
        if is_proteomics:
            cols_weights.append('protein')
        cols_weights.extend(['rsid', 'varID', 'ref_allele', 'eff_allele','weight'])
        cur.execute("DROP TABLE IF EXISTS weights;")
        cur.execute(f"CREATE TABLE weights({', '.join(cols_weights)})")

        # Table 'sample_info'
        cur.execute("DROP TABLE IF EXISTS sample_info;")
        cur.execute(f'CREATE TABLE sample_info("n.samples")')

        dataset_tissue = dataset.tissue.label
        # dataset_tissue = 'subcutaneous adipose tissue'
        if dataset_tissue in tissues_mapping.keys():
            dataset_dir = tissues_mapping[dataset_tissue]
        else:
            dataset_dir = dataset.id
         
        insert_extra_block = []
        insert_weights_block = []

        # Training samples
        sample_count = 0
        for sample_training in dataset.samples_training.all():
            sample_count += sample_training.sample_number
        if sample_count != 0:
            cur.execute("INSERT INTO sample_info VALUES (?)", (sample_count,))
            con.commit()

        extra_values = '?, ?, ?, ?, ?, ?, ?, ?, ?'
        if is_proteomics:
            extra_values += ', ?'

        # For each score
        scores = Score.objects.filter(dataset=dataset).order_by('num')
        for score in scores:
            genes = score.genes.all()
            gene = genes[0]
            gene_id = gene.external_id
            metrics = {}
            for perf in score.score_performance.all():
                for metric in perf.performance_metric.all():
                    if metric.name_short == 'R2':
                        metrics['R2'] = metric.estimate
                        metrics['R2_pval'] = metric.pvalue
                    elif metric.name_short == 'Rho':
                        metrics['Rho'] = metric.estimate
                        metrics['Rho_pval'] = metric.pvalue

            # 1 - Extract metadata data from DB + insert data in SQLite
            score_data = {
                'omicspred_id': score.id,
                'gene': gene_id, 
                'genename': gene.name,
                'gene_type': gene.biotype
            }
            if is_proteomics:
                proteins = score.proteins.all()
                protein = proteins[0]
                score_data['protein'] = protein.external_id
            score_data['"n.snps.in.model"'] = score.variants_number
            score_data['cv_R2_avg'] = metrics['R2']
            score_data['nested_cv_fisher_pval'] = metrics['R2_pval']
            score_data['rho_avg'] = metrics['Rho']
            score_data['"pred.perf.pval"'] = metrics['Rho_pval']

            data_list = []
            for col in cols_extra:
                data_list.append(score_data[col])
            data2insert = tuple(data_list)
            insert_extra_block.append(data2insert)

            if len(insert_extra_block) == insert_block_max:
                cur.executemany(f"INSERT INTO extra VALUES({extra_values})", insert_extra_block)
                con.commit()
                insert_extra_block = []

            # 2 - Extract data from file + insert data in SQLite
            molecular_traits = {'gene_id': gene_id}
            weights_values = '?, ?, ?, ?, ?, ?, ?'
            if is_proteomics:
                molecular_traits['protein_id'] = protein.external_id
                weights_values += ', ?'
            insert_weights_block = read_scoring_file(scoring_files_dir,dataset_dir,score.id,molecular_traits)
           
            cur.executemany(f"INSERT INTO weights VALUES({weights_values})", insert_weights_block)
            con.commit()

        # TODO: place in function to avoid code duplication
        if len(insert_extra_block) != 0:
            cur.executemany(f"INSERT INTO extra VALUES({extra_values})", insert_extra_block)
            con.commit()
            insert_extra_block = []

    con.close()