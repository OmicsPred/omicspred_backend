import os, io, sys
import re
import sqlite3
import pathlib
import zipfile
import datetime
from omicspred.models import *

# OPGS018874.txt

#omicspred_id=OPGS018874
#pgs_name=OID21306
#trait_type=proteomics
#measurement_tissue=plasma
#measurement_platform=Olink Explore
#trait_reported=Calbindin
#genome_build=GRCh37
#variants_number=51
#citation=Xu, Y et al. Nature (2023). doi:10.1038/s41586-023-05844-9
#license=CC BY
# rsID	chr_name	chr_position	effect_allele	other_allele	effect_weight
# rs4703712	5	75839350	C	A	-0.0367272447198089
# rs3797378	5	75887658	C	T	-0.0227123242438836
# rs4704344	5	75898225	C	T	-0.0080439617180173

# +-------------------+------------+----------------------+------------+------------+---------------------+
# |       gene        |    rsid    |        varID         | ref_allele | eff_allele |       weight        |
# +-------------------+------------+----------------------+------------+------------+---------------------+
# | ENSG00000261456.5 | rs11252127 | chr10_52147_C_T_b38  | C          | T          | 0.0522527061423131  |
# | ENSG00000261456.5 | rs11252546 | chr10_58487_T_C_b38  | T          | C          | -0.0335449590056556 |


pmid = 32913098
ds_name = '- sQTL - Enet -'

# Enet eQTL
# dbs_location = '/Users/lg10/Workspace/datafiles/OmicsPred/GTEx_V8/elastic_net_models/'
# scores_root_dir = '/Users/lg10/Workspace/datafiles/OmicsPred/GTEx_V8/genetic_scores'

# Enet sQTL
dbs_location = '/Users/lg10/Workspace/datafiles/OmicsPred/GTEx_V8/elastic_net_models_splicing/'
scores_root_dir = '/Users/lg10/Workspace/datafiles/OmicsPred/GTEx_V8/genetic_scores_enet_splicing'

# datasets_list = {
#     'Adipose_Subcutaneous': {'tissue_id': 'UBERON_0002190', 'db':'gtex_splicing_v8_eur_Adipose_Subcutaneous_signif.db'}
# }

datasets_list = {
    'Adipose_Subcutaneous': {'tissue_id': 'UBERON_0002190', 'db':'gtex_splicing_v8_eur_Adipose_Subcutaneous_signif.db'},
    'Adipose_Visceral_Omentum': {'tissue_id': 'UBERON_0010414', 'db':'gtex_splicing_v8_eur_Adipose_Visceral_Omentum_signif.db'},
    'Adrenal_Gland': {'tissue_id': 'UBERON_0002369', 'db':'gtex_splicing_v8_eur_Adrenal_Gland_signif.db'},
    'Artery_Aorta': {'tissue_id': 'UBERON_0001496', 'db':'gtex_splicing_v8_eur_Artery_Aorta_signif.db'},
    'Artery_Coronary': {'tissue_id': 'UBERON_0001621', 'db':'gtex_splicing_v8_eur_Artery_Coronary_signif.db'},
    'Artery_Tibial': {'tissue_id': 'UBERON_0007610', 'db':'gtex_splicing_v8_eur_Artery_Tibial_signif.db'},
    'Brain_Amygdala': {'tissue_id': 'UBERON_0001876', 'db':'gtex_splicing_v8_eur_Brain_Amygdala_signif.db'},
    'Brain_Anterior_cingulate_cortex_BA24': {'tissue_id': 'UBERON_0009835', 'db':'gtex_splicing_v8_eur_Brain_Anterior_cingulate_cortex_BA24_signif.db'},
    'Brain_Caudate_basal_ganglia': {'tissue_id': 'UBERON_0001873', 'db':'gtex_splicing_v8_eur_Brain_Caudate_basal_ganglia_signif.db'},
    'Brain_Cerebellar_Hemisphere': {'tissue_id': 'UBERON_0002245', 'db':'gtex_splicing_v8_eur_Brain_Cerebellar_Hemisphere_signif.db'},
    'Brain_Cerebellum': {'tissue_id': 'UBERON_0002037', 'db':'gtex_splicing_v8_eur_Brain_Cerebellum_signif.db'},
    'Brain_Cortex': {'tissue_id': 'UBERON_0001870', 'db':'gtex_splicing_v8_eur_Brain_Cortex_signif.db'},
    'Brain_Frontal_Cortex_BA9': {'tissue_id': 'UBERON_0009834', 'db':'gtex_splicing_v8_eur_Brain_Frontal_Cortex_BA9_signif.db'},
    'Brain_Hippocampus': {'tissue_id': 'UBERON_0001954', 'db':'gtex_splicing_v8_eur_Brain_Hippocampus_signif.db'},
    'Brain_Hypothalamus': {'tissue_id': 'UBERON_0001898', 'db':'gtex_splicing_v8_eur_Brain_Hypothalamus_signif.db'},
    'Brain_Nucleus_accumbens_basal_ganglia': {'tissue_id': 'UBERON_0001882', 'db':'gtex_splicing_v8_eur_Brain_Nucleus_accumbens_basal_ganglia_signif.db'},
    'Brain_Putamen_basal_ganglia': {'tissue_id': 'UBERON_0001874', 'db':'gtex_splicing_v8_eur_Brain_Putamen_basal_ganglia_signif.db'},
    'Brain_Spinal_cord_cervical_c-1': {'tissue_id': 'UBERON_0006469', 'db':'gtex_splicing_v8_eur_Brain_Spinal_cord_cervical_c-1_signif.db'},
    'Brain_Substantia_nigra': {'tissue_id': 'UBERON_0002038', 'db':'gtex_splicing_v8_eur_Brain_Substantia_nigra_signif.db'},
    'Breast_Mammary_Tissue': {'tissue_id': 'UBERON_0008367', 'db':'gtex_splicing_v8_eur_Breast_Mammary_Tissue_signif.db'},
    'Cells_Cultured_fibroblasts': {'tissue_id': 'EFO_0002009', 'db':'gtex_splicing_v8_eur_Cells_Cultured_fibroblasts_signif.db'},
    'Cells_EBV-transformed_lymphocytes': {'tissue_id': 'EFO_0000572', 'db':'gtex_splicing_v8_eur_Cells_EBV-transformed_lymphocytes_signif.db'},
    'Colon_Sigmoid': {'tissue_id': 'UBERON_0001159', 'db':'gtex_splicing_v8_eur_Colon_Sigmoid_signif.db'},
    'Colon_Transverse': {'tissue_id': 'UBERON_0001157', 'db':'gtex_splicing_v8_eur_Colon_Transverse_signif.db'},
    'Esophagus_Gastroesophageal_Junction': {'tissue_id': 'UBERON_0004550', 'db':'gtex_splicing_v8_eur_Esophagus_Gastroesophageal_Junction_signif.db'},
    'Esophagus_Mucosa': {'tissue_id': 'UBERON_0006920', 'db':'gtex_splicing_v8_eur_Esophagus_Mucosa_signif.db'},
    'Esophagus_Muscularis': {'tissue_id': 'UBERON_0004648', 'db':'gtex_splicing_v8_eur_Esophagus_Muscularis_signif.db'},
    'Heart_Atrial_Appendage': {'tissue_id': 'UBERON_0006631', 'db':'gtex_splicing_v8_eur_Heart_Atrial_Appendage_signif.db'},
    'Heart_Left_Ventricle': {'tissue_id': 'UBERON_0006566', 'db':'gtex_splicing_v8_eur_Heart_Left_Ventricle_signif.db'},
    'Kidney_Cortex': {'tissue_id': 'UBERON_0001225', 'db':'gtex_splicing_v8_eur_Kidney_Cortex_signif.db'},
    'Liver': {'tissue_id': 'UBERON_0001114', 'db':'gtex_splicing_v8_eur_Liver_signif.db'},
    'Lung': {'tissue_id': 'UBERON_0008952', 'db':'gtex_splicing_v8_eur_Lung_signif.db'},
    'Minor_Salivary_Gland': {'tissue_id': 'UBERON_0006330', 'db':'gtex_splicing_v8_eur_Minor_Salivary_Gland_signif.db'},
    'Muscle_Skeletal': {'tissue_id': 'UBERON_0011907', 'db':'gtex_splicing_v8_eur_Muscle_Skeletal_signif.db'},
    'Nerve_Tibial': {'tissue_id': 'UBERON_0001323', 'db':'gtex_splicing_v8_eur_Nerve_Tibial_signif.db'},
    'Ovary': {'tissue_id': 'UBERON_0000992', 'db':'gtex_splicing_v8_eur_Ovary_signif.db'},
    'Pancreas': {'tissue_id': 'UBERON_0001150', 'db':'gtex_splicing_v8_eur_Pancreas_signif.db'},
    'Pituitary': {'tissue_id': 'UBERON_0000007', 'db':'gtex_splicing_v8_eur_Pituitary_signif.db'},
    'Prostate': {'tissue_id': 'UBERON_0002367', 'db':'gtex_splicing_v8_eur_Prostate_signif.db'},
    'Skin_Not_Sun_Exposed_Suprapubic': {'tissue_id': 'UBERON_0036149', 'db':'gtex_splicing_v8_eur_Skin_Not_Sun_Exposed_Suprapubic_signif.db'},
    'Skin_Sun_Exposed_Lower_leg': {'tissue_id': 'UBERON_0004264', 'db':'gtex_splicing_v8_eur_Skin_Sun_Exposed_Lower_leg_signif.db'},
    'Small_Intestine_Terminal_Ileum': {'tissue_id': 'UBERON_0001211', 'db':'gtex_splicing_v8_eur_Small_Intestine_Terminal_Ileum_signif.db'},
    'Spleen': {'tissue_id': 'UBERON_0002106', 'db':'gtex_splicing_v8_eur_Spleen_signif.db'},
    'Stomach': {'tissue_id': 'UBERON_0000945', 'db':'gtex_splicing_v8_eur_Stomach_signif.db'},
    'Testis': {'tissue_id': 'UBERON_0000473', 'db':'gtex_splicing_v8_eur_Testis_signif.db'},
    'Thyroid': {'tissue_id': 'UBERON_0002046', 'db':'gtex_splicing_v8_eur_Thyroid_signif.db'},
    'Uterus': {'tissue_id': 'UBERON_0000995', 'db':'gtex_splicing_v8_eur_Uterus_signif.db'},
    'Vagina': {'tissue_id': 'UBERON_0000996', 'db':'gtex_splicing_v8_eur_Vagina_signif.db'},
    'Whole_Blood': {'tissue_id': 'UBERON_0013756', 'db':'gtex_splicing_v8_eur_Whole_Blood_signif.db'}
}


def get_dataset(pmid:int, tissue_id:str, name:str) -> Dataset:
    ''' Fetch the corresponding Dataset from the database '''
    try:
        dataset = Dataset.objects.get(publication__pmid=pmid, tissue__id=tissue_id, name__icontains=name)
        return dataset
    except Dataset.DoesNotExist:
        print(f"Can't find the dataset with PMID:{pmid} and Tissue ID '{tissue_id}'")
        exit(0)


def get_score_molecular_trait(score:Score) -> str:
    ''' Extract the molecular trait ID associated with the score '''
    # intron_1_999787_999866_Vagina_GTExV8
    score_name = score.name
    if score_name.startswith('intron_'):
        intron = re.match(r'^(intron_\w+_\d+_\d+)',score_name)
        return intron.group(1)
    else:
        return score.trait_reported_id


def get_genetic_score_data(sqlite_cursor:sqlite3.Cursor,reported_trait_id:str) -> sqlite3.Cursor:
    ''' Build and execute the SQL query to fetch the genetic score variant information from the SQLite database. '''
    # print(f"SELECT rsid, ref_allele, eff_allele, weight FROM weights WHERE gene='{reported_trait_id}';")
    qcursor = sqlite_cursor.execute(f"SELECT rsid, ref_allele, eff_allele, weight FROM weights WHERE gene='{reported_trait_id}';")
    return qcursor


def build_zip_file(scores_root_dir:str, dataset_directory:pathlib.Path, dataset_label:str):
    ''' Generate the zip file of the directory '''
    zipfile_name = f'{scores_root_dir}/{dataset_label}.zip'
    with zipfile.ZipFile(zipfile_name, 'w') as archive:
        for scoring_file_path in dataset_directory.iterdir():
            archive.write(scoring_file_path, arcname=scoring_file_path.name)

    # Check that the zip file exists and is not empty 
    if not os.path.exists(zipfile_name):
        print(f"ERROR: the zipped file '{zipfile_name}' doesn't exist")
        exit(1)
    elif os.path.getsize(zipfile_name) == 0:
        print(f"ERROR: the zipped file '{zipfile_name}' is empty")
        exit(1)


def write_header(filehandle:io.TextIOWrapper, score:Score, dataset:Dataset):
    '''
        Build and write the scoring file header, e.g.:
            #omicspred_id=OPGS018874
            #pgs_name=OID21306
            #trait_type=proteomics
            #measurement_tissue=plasma
            #measurement_platform=Olink Explore
            #trait_reported=Calbindin
            #genome_build=GRCh37
            #variants_number=51
            #note=Model extracted as-is from PredictDB.org
            #citation=Xu, Y et al. Nature (2023). doi:10.1038/s41586-023-05844-9
            #license=CC BY
    '''
    # Score ID
    write_row(filehandle, f'#omicspred_id={score.id}')
    # Score name
    if score.name:
        write_row(filehandle, f'#pgs_name={score.name}')
    # Omics type
    write_row(filehandle, f'#trait_type={dataset.platform.platform_master.type.lower()}')
    # Tissue
    write_row(filehandle, f'#measurement_tissue={dataset.tissue.label} ({dataset.tissue.id})')
    # Platform
    platform = dataset.platform.name
    if dataset.platform.version:
        platform += f' - {dataset.platform.version}'
    write_row(filehandle, f'#measurement_platform={platform}')
    # Reported molecular trait
    if score.trait_reported:
        write_row(filehandle, f'#trait_reported={score.trait_reported} ({score.trait_reported_id})')
    # Genome build
    write_row(filehandle, f'#genome_build={score.variants_genomebuild}')
    # Variants number
    write_row(filehandle, f'#variants_number={score.variants_number}')
    # Note/Comment
    if score.comment:
        write_row(filehandle, f'#note={score.comment}')
    # Citation
    publication = dataset.publication
    year_publication = publication.pub_year
    citation = f'{publication.firstauthor} et al. {publication.journal} ({year_publication}). doi:{publication.doi}'
    write_row(filehandle, f'#citation={citation}')
    write_row(filehandle, f'#license={score.license}')


def write_row(filehandle:io.TextIOWrapper,row_content:str,order:int=2):
    ''' Write a new row in the scoring file '''
    if order==0:
        filehandle.write(row_content)
    elif order==1:
        filehandle.write(f'\n{row_content}')
    elif order==2:
        filehandle.write(f'{row_content}\n')


def run():

    start_time = datetime.now()
    print(f"Start time: {start_time}")

    datasets_count = len(datasets_list.keys())
    dataset_number = 1

    for dataset_label in datasets_list.keys():
        print(f"# Dataset {dataset_label} ({dataset_number}/{datasets_count})")
        dataset_number += 1
        # 1 - Create directory
        # Root directory
        if not os.path.isdir(scores_root_dir):
            print("  - Create root directory")
            os.mkdir(scores_root_dir)
        # Dataset directory
        dataset_dir = f'{scores_root_dir}/{dataset_label}'
        if not os.path.isdir(dataset_dir):
            print(f"  - Create dataset directory")
            os.mkdir(dataset_dir)

        # 2 - Fetch scores and dataset
        print("  - Get dataset")
        dataset = get_dataset(pmid,datasets_list[dataset_label]['tissue_id'],ds_name)
        
        sqlite_file = dbs_location+datasets_list[dataset_label]['db']
        sqlite_connection = sqlite3.connect(sqlite_file)
        sqlite_cursor = sqlite_connection.cursor()

        genetic_scores = {}
        scores = Score.objects.filter(dataset=dataset)
        scores_count = Score.objects.filter(dataset=dataset).count()

        # 3 - Extract variant data and build genetic scores files
        print("  - Get variant data from SQLite database for each genetic score of the current dataset & build scoring files")
        for score in scores:
            score_id = score.id
            genetic_scores[score_id] = []
            # score_trait = score.trait_reported_id
            score_trait = get_score_molecular_trait(score)
            scoring_file_name = f'{dataset_dir}/{score_id}.txt'
            # Scoring file
            file = open(scoring_file_name,'w')
            # 3a - Generate header content
            write_header(file,score,dataset)
            qcursor = get_genetic_score_data(sqlite_cursor,score_trait)
            # 3b - Generate variants content
            write_row(file,'rsID\teffect_allele\tother_allele\teffect_weight')
            first_row = True
            count_rows = 0
            for row in qcursor:
                rsid, ref_allele, eff_allele, weight = row
                row_string = f'{rsid}\t{eff_allele}\t{ref_allele}\t{weight}'
                if first_row:
                    write_row(file,row_string,0)
                    first_row = False
                else:
                    write_row(file,row_string,1)
                count_rows += 1
                # genetic_scores[score_id].append({
                #     'rsID': rsID,
                #     'effect_allele': eff_allele,
                #     'other_allele': ref_allele,
                #     'effect_weight': weight
                # })
            file.close()
            if count_rows != score.variants_number:
                print(f"    >> Score {score_id}: discrepancies between the number of variants in metadata ({score.variants_number}) and sqlite ({count_rows}).")
        sqlite_cursor.close()
        sqlite_connection.close()

        # 4 - Build zip file for the dataset
        print("  - Build Zip file")
        dataset_directory = pathlib.Path(dataset_dir)
        count_files = len(list(dataset_directory.glob('*')))
        if scores_count == count_files:
            build_zip_file(scores_root_dir, dataset_directory, dataset_label)
        else:
            print(f"    >> Zip file error: the number of Genetic Scores ({scores_count}) differs from the number of scoring files generated ({count_files}) ")
            sys.exit()

    end_time = datetime.now()
    print(f"Started time: {start_time}")
    print(f"Ended time: {end_time}")

