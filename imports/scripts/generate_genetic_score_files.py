import os, io, sys
import sqlite3
import pathlib
import zipfile
import datetime
from omicspred.models import *

# OPGS018874_model.txt

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
# rsid	chr_name	chr_position	effect_allele	other_allele	effect_weight
# rs4703712	5	75839350	C	A	-0.0367272447198089
# rs3797378	5	75887658	C	T	-0.0227123242438836
# rs4704344	5	75898225	C	T	-0.0080439617180173

# +-------------------+------------+----------------------+------------+------------+---------------------+
# |       gene        |    rsid    |        varID         | ref_allele | eff_allele |       weight        |
# +-------------------+------------+----------------------+------------+------------+---------------------+
# | ENSG00000261456.5 | rs11252127 | chr10_52147_C_T_b38  | C          | T          | 0.0522527061423131  |
# | ENSG00000261456.5 | rs11252546 | chr10_58487_T_C_b38  | T          | C          | -0.0335449590056556 |


pmid = 26258848

dbs_location = '/Users/lg10/Workspace/datafiles/OmicsPred/GTEx_V8/elastic_net_models/'
scores_root_dir = '/Users/lg10/Workspace/datafiles/OmicsPred/GTEx_V8/genetic_scores'


datasets_list = {
    'Adipose_Subcutaneous': {'tissue_id': 'UBERON_0002190', 'db':'en_Adipose_Subcutaneous.db'},
    'Adipose_Visceral_Omentum': {'tissue_id': 'UBERON_0010414', 'db':'en_Adipose_Visceral_Omentum.db'},
    'Adrenal_Gland': {'tissue_id': 'UBERON_0002369', 'db':'en_Adrenal_Gland.db'},
    'Artery_Aorta': {'tissue_id': 'UBERON_0001496', 'db':'en_Artery_Aorta.db'},
    'Artery_Coronary': {'tissue_id': 'UBERON_0001621', 'db':'en_Artery_Coronary.db'},
    'Artery_Tibial': {'tissue_id': 'UBERON_0007610', 'db':'en_Artery_Tibial.db'},
    'Brain_Amygdala': {'tissue_id': 'UBERON_0001876', 'db':'en_Brain_Amygdala.db'},
    'Brain_Anterior_cingulate_cortex_BA24': {'tissue_id': 'UBERON_0009835', 'db':'en_Brain_Anterior_cingulate_cortex_BA24.db'},
    'Brain_Caudate_basal_ganglia': {'tissue_id': 'UBERON_0001873', 'db':'en_Brain_Caudate_basal_ganglia.db'},
    'Brain_Cerebellar_Hemisphere': {'tissue_id': 'UBERON_0002245', 'db':'en_Brain_Cerebellar_Hemisphere.db'},
    'Brain_Cerebellum': {'tissue_id': 'UBERON_0002037', 'db':'en_Brain_Cerebellum.db'},
    'Brain_Cortex': {'tissue_id': 'UBERON_0001870', 'db':'en_Brain_Cortex.db'},
    'Brain_Frontal_Cortex_BA9': {'tissue_id': 'UBERON_0009834', 'db':'en_Brain_Frontal_Cortex_BA9.db'},
    'Brain_Hippocampus': {'tissue_id': 'UBERON_0001954', 'db':'en_Brain_Hippocampus.db'},
    'Brain_Hypothalamus': {'tissue_id': 'UBERON_0001898', 'db':'en_Brain_Hypothalamus.db'},
    'Brain_Nucleus_accumbens_basal_ganglia': {'tissue_id': 'UBERON_0001882', 'db':'en_Brain_Nucleus_accumbens_basal_ganglia.db'},
    # 'Brain_Putamen_basal_ganglia': {'tissue_id': 'UBERON_0001874', 'db':'en_Brain_Putamen_basal_ganglia.db'},
    'Brain_Spinal_cord_cervical_c-1': {'tissue_id': 'UBERON_0006469', 'db':'en_Brain_Spinal_cord_cervical_c-1.db'},
    'Brain_Substantia_nigra': {'tissue_id': 'UBERON_0002038', 'db':'en_Brain_Substantia_nigra.db'},
    'Breast_Mammary_Tissue': {'tissue_id': 'UBERON_0008367', 'db':'en_Breast_Mammary_Tissue.db'},
    'Cells_Cultured_fibroblasts': {'tissue_id': 'EFO_0002009', 'db':'en_Cells_Cultured_fibroblasts.db'},
    'Cells_EBV-transformed_lymphocytes': {'tissue_id': 'EFO_0000572', 'db':'en_Cells_EBV-transformed_lymphocytes.db'},
    'Colon_Sigmoid': {'tissue_id': 'UBERON_0001159', 'db':'en_Colon_Sigmoid.db'},
    'Colon_Transverse': {'tissue_id': 'UBERON_0001157', 'db':'en_Colon_Transverse.db'},
    'Esophagus_Gastroesophageal_Junction': {'tissue_id': 'UBERON_0004550', 'db':'en_Esophagus_Gastroesophageal_Junction.db'},
    'Esophagus_Mucosa': {'tissue_id': 'UBERON_0006920', 'db':'en_Esophagus_Mucosa.db'},
    'Esophagus_Muscularis': {'tissue_id': 'UBERON_0004648', 'db':'en_Esophagus_Muscularis.db'},
    'Heart_Atrial_Appendage': {'tissue_id': 'UBERON_0006631', 'db':'en_Heart_Atrial_Appendage.db'},
    'Heart_Left_Ventricle': {'tissue_id': 'UBERON_0006566', 'db':'en_Heart_Left_Ventricle.db'},
    'Kidney_Cortex': {'tissue_id': 'UBERON_0001225', 'db':'en_Kidney_Cortex.db'},
    'Liver': {'tissue_id': 'UBERON_0001114', 'db':'en_Liver.db'},
    'Lung': {'tissue_id': 'UBERON_0008952', 'db':'en_Lung.db'},
    'Minor_Salivary_Gland': {'tissue_id': 'UBERON_0006330', 'db':'en_Minor_Salivary_Gland.db'},
    'Muscle_Skeletal': {'tissue_id': 'UBERON_0011907', 'db':'en_Muscle_Skeletal.db'},
    'Nerve_Tibial': {'tissue_id': 'UBERON_0001323', 'db':'en_Nerve_Tibial.db'},
    'Ovary': {'tissue_id': 'UBERON_0000992', 'db':'en_Ovary.db'},
    'Pancreas': {'tissue_id': 'UBERON_0001150', 'db':'en_Pancreas.db'},
    'Pituitary': {'tissue_id': 'UBERON_0000007', 'db':'en_Pituitary.db'},
    'Prostate': {'tissue_id': 'UBERON_0002367', 'db':'en_Prostate.db'},
    'Skin_Not_Sun_Exposed_Suprapubic': {'tissue_id': 'UBERON_0036149', 'db':'en_Skin_Not_Sun_Exposed_Suprapubic.db'},
    'Skin_Sun_Exposed_Lower_leg': {'tissue_id': 'UBERON_0004264', 'db':'en_Skin_Sun_Exposed_Lower_leg.db'},
    'Small_Intestine_Terminal_Ileum': {'tissue_id': 'UBERON_0001211', 'db':'en_Small_Intestine_Terminal_Ileum.db'},
    'Spleen': {'tissue_id': 'UBERON_0002106', 'db':'en_Spleen.db'},
    'Stomach': {'tissue_id': 'UBERON_0000945', 'db':'en_Stomach.db'},
    'Testis': {'tissue_id': 'UBERON_0000473', 'db':'en_Testis.db'},
    'Thyroid': {'tissue_id': 'UBERON_0002046', 'db':'en_Thyroid.db'},
    'Uterus': {'tissue_id': 'UBERON_0000995', 'db':'en_Uterus.db'},
    'Vagina': {'tissue_id': 'UBERON_0000996', 'db':'en_Vagina.db'},
    'Whole_Blood': {'tissue_id': 'UBERON_0013756', 'db':'en_Whole_Blood.db'}
}


def get_dataset(pmid:int, tissue_id:str) -> Dataset:
    ''' Fetch the corresponding Dataset from the database '''
    try:
        dataset = Dataset.objects.get(publication__pmid=pmid, tissue__id=tissue_id)
        return dataset
    except Dataset.DoesNotExist:
        print(f"Can't find the dataset with PMID:{pmid} and Tissue ID '{tissue_id}'")
        exit(0)


def get_genetic_score_data(sqlite_cursor:sqlite3.Cursor,reported_trait_id:str) -> sqlite3.Cursor:
    ''' Build and execute the SQL query to fetch the genetic score variant information from the SQLite database. '''
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
    write_row(filehandle, f'#measurement_tissue={dataset.tissue.label}')
    # Platform
    platform = dataset.platform.name
    if dataset.platform.version:
        platform += f' {dataset.platform.version}'
    write_row(filehandle, f'#measurement_platform={platform}')
    # Reported molecular trait
    if score.trait_reported:
        write_row(filehandle, f'#trait_reported={score.trait_reported}')
    # Genome build
    write_row(filehandle, f'#genome_build={score.variants_genomebuild}')
    # Variants number
    write_row(filehandle, f'#variants_number={score.variants_number}')
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
        dataset = get_dataset(pmid,datasets_list[dataset_label]['tissue_id'])
        
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
            score_trait = score.trait_reported_id
            scoring_file_name = f'{dataset_dir}/{score_id}_model.txt'
            # Scoring file
            file = open(scoring_file_name,'w')
            # 3a - Generate header content
            write_header(file,score,dataset)
            qcursor = get_genetic_score_data(sqlite_cursor,score_trait)
            # 3b - Generate variants content
            write_row(file,'rsid\teffect_allele\tother_allele\teffect_weight')
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
                #     'rsid': rsid,
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

