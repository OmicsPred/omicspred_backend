import os, io
import sqlite3
import pathlib
import zipfile
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
    'Adipose_Subcutaneous': {'tissue_id': 'UBERON_0002190', 'db':'en_Adipose_Subcutaneous.db'}
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


def build_zip_file(scores_root_dir:str, dataset_dir:str, dataset_label:str):
    ''' Generate the zip file of the directory '''
    dataset_directory = pathlib.Path(dataset_dir)
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

    for dataset_label in datasets_list.keys():
        # 1 - Create directory
        # Root directory
        if not os.path.isdir(scores_root_dir):
            print("# Create root directory")
            os.mkdir(scores_root_dir)
        # Dataset directory
        dataset_dir = f'{scores_root_dir}/{dataset_label}'
        if not os.path.isdir(dataset_dir):
            print(f"# Create dataset directory '{dataset_label}'")
            os.mkdir(dataset_dir)

        # 2 - Fetch scores and dataset
        print("# Get dataset")
        dataset = get_dataset(pmid,datasets_list[dataset_label]['tissue_id'])
        
        sqlite_file = dbs_location+datasets_list[dataset_label]['db']
        sqlite_connection = sqlite3.connect(sqlite_file)
        sqlite_cursor = sqlite_connection.cursor()

        genetic_scores = {}
        scores = Score.objects.filter(dataset=dataset)

        # 3 - Extract variant data and build genetic scores files
        print("# Get variant data from SQLite database for each genetic score of the current dataset & build scoring files")
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
            for row in qcursor:
                rsid, ref_allele, eff_allele, weight = row
                row_string = f'{rsid}\t{eff_allele}\t{ref_allele}\t{weight}'
                if first_row:
                    write_row(file,row_string,0)
                    first_row = False
                else:
                    write_row(file,row_string,1)
                # genetic_scores[score_id].append({
                #     'rsid': rsid,
                #     'effect_allele': eff_allele,
                #     'other_allele': ref_allele,
                #     'effect_weight': weight
                # })
            file.close()
        sqlite_cursor.close()
        sqlite_connection.close()

        # 4 - Build zip file for the dataset
        print("# Build Zip file")
        build_zip_file(scores_root_dir, dataset_dir, dataset_label)

