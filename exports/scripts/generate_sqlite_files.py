from omicspred.models import *
from exports.sqlite_export import SqliteExport
from exports.config import sqlite_default_values


insert_block_max = 100

gtex_prefix_study = 'GTExV8'

if 'use_different_id_as_gene' in sqlite_default_values.keys():
    use_different_id_as_gene = sqlite_default_values['use_different_id_as_gene']
else:
    use_different_id_as_gene = None

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
# For GTEx study
methods_mapping = {
    'Enet': 'Elastic Net',
    'MASHR': 'MASHR'
}
platforms_mapping = {
    'eQTL': 'RNAseq - Expression',
    'sQTL': 'RNAseq - Splicing'
}


def run(*args):
    skip_zip = False

    if args:
        opp_id = args[0]
        output_sqlite_dir = args[1]
        scoring_files_dir = args[2]
        skip_zip = args[3]
    else:
        opp_id = sqlite_default_values['opp_id']
        output_sqlite_dir = sqlite_default_values['sqlite_dir']
        scoring_files_dir = sqlite_default_values['scoring_files_dir']
        if 'skip_zip' in sqlite_default_values.keys():
            skip_zip = sqlite_default_values['skip_zip']

    # Fetch dataset(s)
    datasets = Dataset.objects.filter(publication__id=opp_id).order_by('id')
    # Create SqliteExport object
    sqlite_export = SqliteExport(opp_id,output_sqlite_dir,scoring_files_dir,datasets,use_different_id_as_gene)
    # Generate SQLite export file(s)
    sqlite_export.generate_sqlite_files(skip_zip)