import os, io, sys
import re
import requests
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
# or
# +------------------------------+------------------------+------------------------+------------+------------+----------------------+
# |             gene             |          rsid          |         varID          | ref_allele | eff_allele |        weight        |
# +------------------------------+------------------------+------------------------+------------+------------+----------------------+
# | intron_4_127656721_127663381 | chr4_127656228_T_C_b38 | chr4_127656228_T_C_b38 | T          | C          | -0.0176620830039489  |
# | intron_4_127656721_127663381 | rs75447657             | chr4_127656435_T_G_b38 | T          | G          | 0.000292301470797823 |

pmid = 32913098
project_dir = '/Users/lg10/Workspace/datafiles/OmicsPred/'
variant_coords_sqlite_db_file = f'{project_dir}op_variant_coords.db'

# Enet eQTL
# dbs_location = f'{project_dir}/GTEx_V8/elastic_net_models_expression/'
# scores_root_dir = f'{project_dir}/GTEx_V8/scoring_files/genetic_scores_enet_expression'
# file_prefix = 'en_'
# file_suffix = ''
# ds_name = '- eQTL - Enet -'

# Enet sQTL
# dbs_location = f'{project_dir}/GTEx_V8/elastic_net_models_splicing/'
# scores_root_dir = f'{project_dir}/GTEx_V8/scoring_files/genetic_scores_enet_splicing'
# file_prefix = 'gtex_splicing_v8_eur_'
# file_suffix = '_signif'
# ds_name = '- sQTL - Enet -'


# # MASHR eQTL
# dbs_location = f'{project_dir}/GTEx_V8/mashr_models_expression/'
# scores_root_dir = f'{project_dir}/GTEx_V8/scoring_files/genetic_scores_mashr_expression'
# file_prefix = 'mashr_'
# file_suffix = ''
# ds_name = '- eQTL - MASHR -'

# MASHR sQTL
dbs_location = f'{project_dir}/GTEx_V8/mashr_models_splicing/'
scores_root_dir = f'{project_dir}/GTEx_V8/scoring_files/genetic_scores_mashr_splicing'
file_prefix = 'mashr_'
file_suffix = ''
ds_name = '- sQTL - MASHR -'


datasets_info_test = {
    'Adipose_Subcutaneous': {'tissue_id': 'UBERON_0002190', 'db':f'{file_prefix}Adipose_Subcutaneous{file_suffix}.db'}
}
datasets_info = {
    'Adipose_Subcutaneous': {'tissue_id': 'UBERON_0002190', 'db':f'{file_prefix}Adipose_Subcutaneous{file_suffix}.db'},
    'Adipose_Visceral_Omentum': {'tissue_id': 'UBERON_0010414', 'db':f'{file_prefix}Adipose_Visceral_Omentum{file_suffix}.db'},
    'Adrenal_Gland': {'tissue_id': 'UBERON_0002369', 'db':f'{file_prefix}Adrenal_Gland{file_suffix}.db'},
    'Artery_Aorta': {'tissue_id': 'UBERON_0001496', 'db':f'{file_prefix}Artery_Aorta{file_suffix}.db'},
    'Artery_Coronary': {'tissue_id': 'UBERON_0001621', 'db':f'{file_prefix}Artery_Coronary{file_suffix}.db'},
    'Artery_Tibial': {'tissue_id': 'UBERON_0007610', 'db':f'{file_prefix}Artery_Tibial{file_suffix}.db'},
    'Brain_Amygdala': {'tissue_id': 'UBERON_0001876', 'db':f'{file_prefix}Brain_Amygdala{file_suffix}.db'},
    'Brain_Anterior_cingulate_cortex_BA24': {'tissue_id': 'UBERON_0009835', 'db':f'{file_prefix}Brain_Anterior_cingulate_cortex_BA24{file_suffix}.db'},
    'Brain_Caudate_basal_ganglia': {'tissue_id': 'UBERON_0001873', 'db':f'{file_prefix}Brain_Caudate_basal_ganglia{file_suffix}.db'},
    'Brain_Cerebellar_Hemisphere': {'tissue_id': 'UBERON_0002245', 'db':f'{file_prefix}Brain_Cerebellar_Hemisphere{file_suffix}.db'},
    'Brain_Cerebellum': {'tissue_id': 'UBERON_0002037', 'db':f'{file_prefix}Brain_Cerebellum{file_suffix}.db'},
    'Brain_Cortex': {'tissue_id': 'UBERON_0001870', 'db':f'{file_prefix}Brain_Cortex{file_suffix}.db'},
    'Brain_Frontal_Cortex_BA9': {'tissue_id': 'UBERON_0009834', 'db':f'{file_prefix}Brain_Frontal_Cortex_BA9{file_suffix}.db'},
    'Brain_Hippocampus': {'tissue_id': 'UBERON_0001954', 'db':f'{file_prefix}Brain_Hippocampus{file_suffix}.db'},
    'Brain_Hypothalamus': {'tissue_id': 'UBERON_0001898', 'db':f'{file_prefix}Brain_Hypothalamus{file_suffix}.db'},
    'Brain_Nucleus_accumbens_basal_ganglia': {'tissue_id': 'UBERON_0001882', 'db':f'{file_prefix}Brain_Nucleus_accumbens_basal_ganglia{file_suffix}.db'},
    'Brain_Putamen_basal_ganglia': {'tissue_id': 'UBERON_0001874', 'db':f'{file_prefix}Brain_Putamen_basal_ganglia{file_suffix}.db'},
    'Brain_Spinal_cord_cervical_c-1': {'tissue_id': 'UBERON_0006469', 'db':f'{file_prefix}Brain_Spinal_cord_cervical_c-1{file_suffix}.db'},
    'Brain_Substantia_nigra': {'tissue_id': 'UBERON_0002038', 'db':f'{file_prefix}Brain_Substantia_nigra{file_suffix}.db'},
    'Breast_Mammary_Tissue': {'tissue_id': 'UBERON_0008367', 'db':f'{file_prefix}Breast_Mammary_Tissue{file_suffix}.db'},
    'Cells_Cultured_fibroblasts': {'tissue_id': 'EFO_0002009', 'db':f'{file_prefix}Cells_Cultured_fibroblasts{file_suffix}.db'},
    'Cells_EBV-transformed_lymphocytes': {'tissue_id': 'EFO_0000572', 'db':f'{file_prefix}Cells_EBV-transformed_lymphocytes{file_suffix}.db'},
    'Colon_Sigmoid': {'tissue_id': 'UBERON_0001159', 'db':f'{file_prefix}Colon_Sigmoid{file_suffix}.db'},
    'Colon_Transverse': {'tissue_id': 'UBERON_0001157', 'db':f'{file_prefix}Colon_Transverse{file_suffix}.db'},
    'Esophagus_Gastroesophageal_Junction': {'tissue_id': 'UBERON_0004550', 'db':f'{file_prefix}Esophagus_Gastroesophageal_Junction{file_suffix}.db'},
    'Esophagus_Mucosa': {'tissue_id': 'UBERON_0006920', 'db':f'{file_prefix}Esophagus_Mucosa{file_suffix}.db'},
    'Esophagus_Muscularis': {'tissue_id': 'UBERON_0004648', 'db':f'{file_prefix}Esophagus_Muscularis{file_suffix}.db'},
    'Heart_Atrial_Appendage': {'tissue_id': 'UBERON_0006631', 'db':f'{file_prefix}Heart_Atrial_Appendage{file_suffix}.db'},
    'Heart_Left_Ventricle': {'tissue_id': 'UBERON_0006566', 'db':f'{file_prefix}Heart_Left_Ventricle{file_suffix}.db'},
    'Kidney_Cortex': {'tissue_id': 'UBERON_0001225', 'db':f'{file_prefix}Kidney_Cortex{file_suffix}.db'},
    'Liver': {'tissue_id': 'UBERON_0001114', 'db':f'{file_prefix}Liver{file_suffix}.db'},
    'Lung': {'tissue_id': 'UBERON_0008952', 'db':f'{file_prefix}Lung{file_suffix}.db'},
    'Minor_Salivary_Gland': {'tissue_id': 'UBERON_0006330', 'db':f'{file_prefix}Minor_Salivary_Gland{file_suffix}.db'},
    'Muscle_Skeletal': {'tissue_id': 'UBERON_0011907', 'db':f'{file_prefix}Muscle_Skeletal{file_suffix}.db'},
    'Nerve_Tibial': {'tissue_id': 'UBERON_0001323', 'db':f'{file_prefix}Nerve_Tibial{file_suffix}.db'},
    'Ovary': {'tissue_id': 'UBERON_0000992', 'db':f'{file_prefix}Ovary{file_suffix}.db'},
    'Pancreas': {'tissue_id': 'UBERON_0001150', 'db':f'{file_prefix}Pancreas{file_suffix}.db'},
    'Pituitary': {'tissue_id': 'UBERON_0000007', 'db':f'{file_prefix}Pituitary{file_suffix}.db'},
    'Prostate': {'tissue_id': 'UBERON_0002367', 'db':f'{file_prefix}Prostate{file_suffix}.db'},
    'Skin_Not_Sun_Exposed_Suprapubic': {'tissue_id': 'UBERON_0036149', 'db':f'{file_prefix}Skin_Not_Sun_Exposed_Suprapubic{file_suffix}.db'},
    'Skin_Sun_Exposed_Lower_leg': {'tissue_id': 'UBERON_0004264', 'db':f'{file_prefix}Skin_Sun_Exposed_Lower_leg{file_suffix}.db'},
    'Small_Intestine_Terminal_Ileum': {'tissue_id': 'UBERON_0001211', 'db':f'{file_prefix}Small_Intestine_Terminal_Ileum{file_suffix}.db'},
    'Spleen': {'tissue_id': 'UBERON_0002106', 'db':f'{file_prefix}Spleen{file_suffix}.db'},
    'Stomach': {'tissue_id': 'UBERON_0000945', 'db':f'{file_prefix}Stomach{file_suffix}.db'},
    'Testis': {'tissue_id': 'UBERON_0000473', 'db':f'{file_prefix}Testis{file_suffix}.db'},
    'Thyroid': {'tissue_id': 'UBERON_0002046', 'db':f'{file_prefix}Thyroid{file_suffix}.db'},
    'Uterus': {'tissue_id': 'UBERON_0000995', 'db':f'{file_prefix}Uterus{file_suffix}.db'},
    'Vagina': {'tissue_id': 'UBERON_0000996', 'db':f'{file_prefix}Vagina{file_suffix}.db'},
    'Whole_Blood': {'tissue_id': 'UBERON_0013756', 'db':f'{file_prefix}Whole_Blood{file_suffix}.db'}
}


datasets_list = datasets_info
# datasets_list = datasets_info_test

rsid_list = {}


def ensembl_rest_call(rsids_list:list):
    # print(f'rsids_list: {rsids_list}')
    data = '["'+'","'.join(rsids_list)+'"]'
    coords = {}
    headers={ "Content-Type" : "application/json", "Accept" : "application/json"}
    rest_url = f'https://rest.ensembl.org/variation/homo_sapiens'
    response = requests.post(rest_url, headers=headers, data='{ "ids": '+data+' }')
    # response = requests.get(rest_url, headers=headers)
    response_json = response.json()
    if response_json:
        if 'error' in response_json.keys():
            return coords
        else:
            for rsid in response_json.keys():
                rsid_entry = response_json[rsid]
                coords[rsid] = {}
                if 'mappings' in rsid_entry.keys():
                    for mapping in rsid_entry['mappings']:
                        if mapping['coord_system'] == 'chromosome':
                            chr_name = mapping['seq_region_name']
                            if str(chr_name) == 'X':
                                chr_name = 23
                            coords[rsid]['chr_name'] = chr_name
                            coords[rsid]['chr_position'] = mapping['start']
    return coords


def get_rsid_coords(sqlite_kb_conn:sqlite3.Connection,rsids_list:list):
    variants_coords = ensembl_rest_call(rsids_list)
    for rsid in variants_coords.keys():
        if variants_coords[rsid]:
            insert_rsid_coords_to_kb(sqlite_kb_conn,rsid,variants_coords[rsid])
            # rsid_list[rsid] = variants_coords[rsid]


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

def get_rsid(sqlite_cursor:sqlite3.Cursor) -> sqlite3.Cursor:
    ''' Build and execute the SQL query to list rsID variants which are associated with non rsID variant, from the SQLite database. '''
    # print(f"SELECT rsid, ref_allele, eff_allele, weight FROM weights WHERE gene='{reported_trait_id}';")
    qcursor = sqlite_cursor.execute("SELECT distinct (rsid) FROM weights WHERE rsid like 'rs%' and gene in (select distinct gene FROM weights WHERE rsid like 'chr%');")
    return qcursor


def count_non_rsid(sqlite_cursor:sqlite3.Cursor,reported_trait_id:str) -> sqlite3.Cursor:
    ''' Build and execute the SQL query to list rsID variants which are associated with non rsID variant, from the SQLite database. '''
    # print(f"SELECT rsid, ref_allele, eff_allele, weight FROM weights WHERE gene='{reported_trait_id}';")
    qcursor = sqlite_cursor.execute(f"SELECT count(distinct rsid) FROM weights WHERE rsid like 'chr%' and gene='{reported_trait_id}';")
    return qcursor.fetchone()[0]


def get_genetic_score_data(sqlite_cursor:sqlite3.Cursor,reported_trait_id:str) -> sqlite3.Cursor:
    ''' Build and execute the SQL query to fetch the genetic score variant information from the SQLite database. '''
    # print(f"SELECT rsid, ref_allele, eff_allele, weight FROM weights WHERE gene='{reported_trait_id}';")
    qcursor = sqlite_cursor.execute(f"SELECT rsid, varID, ref_allele, eff_allele, weight FROM weights WHERE gene='{reported_trait_id}';")
    return qcursor


def check_rsid_is_in_kb(sqlite_kb_conn:sqlite3.Connection,rsid:str) -> sqlite3.Cursor:
    sqlite_kb_cursor = sqlite_kb_conn.cursor()
    qcursor = sqlite_kb_cursor.execute(f"SELECT rsid FROM variant_coords WHERE rsid='{rsid}';")
    result = qcursor.fetchone()
    sqlite_kb_cursor.close()
    return result


def fetch_rsid_coords_from_kb(sqlite_kb_conn:sqlite3.Connection,rsid:str) -> sqlite3.Cursor:
    sqlite_kb_cursor = sqlite_kb_conn.cursor()
    qcursor = sqlite_kb_cursor.execute(f"SELECT chr_name, chr_position FROM variant_coords WHERE rsid='{rsid}';")
    result = qcursor.fetchone()
    sqlite_kb_cursor.close()
    return result


def insert_rsid_coords_to_kb(sqlite_kb_conn:sqlite3.Connection,rsid:str,rsid_coords:dict):
    sqlite_kb_cursor = sqlite_kb_conn.cursor()
    chr_name = rsid_coords['chr_name']
    chr_position = rsid_coords['chr_position']

    # print(f"SQL: INSERT INTO variant_coords (rsid, chr_name, chr_position) VALUES ('{rsid}',{chr_name},{chr_position});")
    sqlite_kb_cursor.execute(f"INSERT OR IGNORE INTO variant_coords (rsid, chr_name, chr_position) VALUES ('{rsid}',{chr_name},{chr_position});")
    sqlite_kb_conn.commit()
    sqlite_kb_cursor.close()


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


def thousandify(number):
    return f'{number:,}'


def run():

    start_time = datetime.now()
    print(f"Start time: {start_time}")

    datasets_count = len(datasets_list.keys())
    dataset_number = 1
    count_rest_api_calls = 0

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


        # 3 - Fetch list of rsID which need chr_name and chr_position
        sqlite_rsid_kb_file = variant_coords_sqlite_db_file
        sqlite_rsid_kb_connection = sqlite3.connect(sqlite_rsid_kb_file)
        # sqlite_rsid_kb_cursor = sqlite_rsid_kb_connection.cursor()

        q_rsid_cursor = get_rsid(sqlite_cursor)
        max_var_list = 50
        rsids_list = set()
        count_variants = 0
        for row in q_rsid_cursor:
            rsid = row[0]
            # print(f"RSID {rsid} FOUND!") #rs35477708
            count_variants += 1
            if str(count_variants).endswith('000') or str(count_variants).endswith('500'):
                print(f"    > {thousandify(count_variants)} rsIDs with coordinates to fetch")
            is_rsid_in_kb = check_rsid_is_in_kb(sqlite_rsid_kb_connection, rsid)
            if not is_rsid_in_kb:
                rsids_list.add(rsid)
            if len(list(rsids_list)) == max_var_list:
                get_rsid_coords(sqlite_rsid_kb_connection,list(rsids_list))
                rsids_list = set()
        if rsids_list:
            get_rsid_coords(sqlite_rsid_kb_connection,list(rsids_list))


        # 4 - Extract variant data and build genetic scores files
        print(f"  - Get variant data from SQLite database for each genetic score of the current dataset & build scoring files ({thousandify(len(scores))} scores)")
        count_ens_calls = 0
        for count_scores, score in enumerate(scores,start=1):
            # if str(count_scores).endswith('0000') or str(count_scores).endswith('5000'):
            if str(count_scores).endswith('0000'):
                print(f"    > {thousandify(count_scores)} scores")
            if str(count_ens_calls).endswith('00'):
                print(f"    >> {thousandify(count_ens_calls)} Ensembl REST API calls")
            count_scores += 1
            score_id = score.id
            genetic_scores[score_id] = []
            # score_trait = score.trait_reported_id
            score_trait = get_score_molecular_trait(score)
            scoring_file_name = f'{dataset_dir}/{score_id}.txt'
            # Scoring file
            file = open(scoring_file_name,'w')
            # 3a - Generate header content
            write_header(file,score,dataset)
            non_rsid_count = count_non_rsid(sqlite_cursor,score_trait)
            qcursor = get_genetic_score_data(sqlite_cursor,score_trait)
            # 3b - Generate variants content
            common_cols='effect_allele\tother_allele\teffect_weight'
            if non_rsid_count:
                write_row(file,f'rsID\tchr_name\tchr_position\t{common_cols}\tvariant_description')
            else:
                write_row(file,f'rsID\t{common_cols}')
            first_row = True
            count_rows = 0
            for row in qcursor:
                rsid, varid, ref_allele, eff_allele, weight = row
                var_desc_content = ''
                if non_rsid_count:
                    var_desc_content = '\t'
                    if rsid.startswith('chr'):
                        variant_id = re.match(r'^chr(\w+)_(\d+)_',rsid)
                        rsid = f'.\t{variant_id.group(1)}\t{variant_id.group(2)}'
                        var_desc_content += f'variant_id={varid}'
                    else:
                        data = fetch_rsid_coords_from_kb(sqlite_rsid_kb_connection, rsid)
                        # if rsid in rsid_list.keys():
                        #     data = rsid_list[rsid]
                        # else:
                        #     data = ensembl_rest_call(rsid)
                        #     count_ens_calls =+ 1
                        #     count_rest_api_calls += 1
                        #     rsid_list[rsid] = data
                        if data:
                            chr_name = data[0]
                            chr_position = data[1]
                            rsid = f'{rsid}\t{chr_name}\t{chr_position}'
                        else:
                            rsid = f'{rsid}\t\t'
                row_string = f'{rsid}\t{eff_allele}\t{ref_allele}\t{weight}{var_desc_content}'
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
                print(f"    >> Score {score_id}: discrepancies between the number of variants in metadata ({thousandify(score.variants_number)}) and sqlite ({thousandify(count_rows)}).")
        print(f"    > {thousandify(count_scores)} scores")
        sqlite_cursor.close()
        sqlite_connection.close()

        # 5 - Build zip file for the dataset
        print("  - Build Zip file")
        dataset_directory = pathlib.Path(dataset_dir)
        count_files = len(list(dataset_directory.glob('*')))
        if scores_count == count_files:
            build_zip_file(scores_root_dir, dataset_directory, dataset_label)
        else:
            print(f"    >> Zip file error: the number of Genetic Scores ({thousandify(scores_count)}) differs from the number of scoring files generated ({thousandify(count_files)}) ")
            sys.exit()

    end_time = datetime.now()
    print(f"Started time: {start_time}")
    print(f"Ended time: {end_time}")
    print(f"Ensembl REST API calls: {thousandify(count_rest_api_calls)}")

