import os
import sqlite3
import gzip
import csv
from omicspred.models import Dataset


covariance_dir = '/Users/lg10/Workspace/datafiles/OmicsPred/PCAIR/covariances'
sqlite_dir = '/Users/lg10/Workspace/datafiles/OmicsPred/PCAIR/sqlite_exports_v2'

publication_id = 4


def fetch_varids(sqlite_file:str) -> list:
    sql_con = sqlite3.connect(f'{sqlite_dir}/{sqlite_file}')
    sql_cur = sql_con.cursor()
    # sql_cur.execute("SELECT distinct gene,rsid,varid FROM weights;")
    sql_cur.execute("SELECT distinct gene,rsid FROM weights;")
    var_table = sql_cur.fetchall()
    sql_cur.close()
    sql_con.close()
    data = {}
    for var_entry in var_table:
        gene = var_entry[0]
        rsid = var_entry[1]
        if gene not in data.keys():
            data[gene] = set()
        data[gene].add(rsid)
    return data


def run():
    sqlite_files = {}
    for file in os.listdir(sqlite_dir):
        if file.endswith('.db'):
            files_parts = file.split('_')
            sqlite_files[files_parts[0]] = file
    
    covariance_files = {}
    for file in os.listdir(covariance_dir):
        if file.endswith('.txt.gz'):
            files_parts = file.split('_')
            covariance_files[files_parts[0]] = file

    datasets = Dataset.objects.filter(publication_id=publication_id).order_by('num')

    for dataset in datasets:
        dataset_id = dataset.id
        missing_genes = 0
        different_rsid1 = 0
        different_rsid2 = 0
        if dataset_id in sqlite_files.keys() and dataset_id in covariance_files.keys():
            print(f'# Dataset {dataset_id} ({dataset.name})')
            varid_list = fetch_varids(sqlite_files[dataset_id])
            varid_list_keys = varid_list.keys()
            with gzip.open(f'{covariance_dir}/{covariance_files[dataset_id]}', 'rt') as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    gene = row['GENE']
                    rsid1 = row['RSID1']
                    rsid2 = row['RSID2']
                    # Checks
                    if gene in varid_list_keys:
                        vars = varid_list[gene]
                        if rsid1 not in vars:
                            different_rsid1 += 1
                        if rsid2 not in vars:
                            different_rsid2 += 1
                    else:
                        missing_genes += 1
            print(f'- missing_genes: {missing_genes}')
            print(f'- different_rsid1: {different_rsid1}')
            print(f'- different_rsid2: {different_rsid2}')

        elif dataset_id in sqlite_files.keys():
            print(f'>> Covariance file missing for {dataset_id}')
        elif dataset_id in covariance_files.keys():
            print(f'>> SQLite file missing for {dataset_id}')
        else:
            print(f'>> SQLite and Covariance files missing for {dataset_id}')

