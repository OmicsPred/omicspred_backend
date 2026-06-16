import os
import sqlite3
import gzip
import csv

class CovarianceValidation:

    # Expected covariance columns
    covariance_columns = ('GENE','RSID1','RSID2','VALUE')

    def __init__(self, covariance_dir:str, sqlite_dir:str, datasets:list,var_type:str):
        self.covariance_dir = covariance_dir
        self.sqlite_dir = sqlite_dir
        self.datasets = datasets # List of Dataset models
        self.dataset_format_checked = []
        self.var_type = var_type # rsid or VarID
        self.variants = set()

        # Get the list of SQLite files in the directory
        self.sqlite_files = {}
        for file in os.listdir(sqlite_dir):
            if file.endswith('.db'):
                files_parts = file.split('_')
                self.sqlite_files[files_parts[0]] = file
        
        # Get the list of covariance files in the directory
        self.covariance_files = {}
        for file in os.listdir(covariance_dir):
            if file.endswith('.txt.gz'):
                files_parts = file.split('_')
                self.covariance_files[files_parts[0]] = file


    def fetch_varids(self, sqlite_file:str) -> list:
        ''' Fetch the variants information from the SQLite DB. '''
        sql_con = sqlite3.connect(f'{self.sqlite_dir}/{sqlite_file}')
        sql_cur = sql_con.cursor()
        sql_statement = "SELECT distinct gene,rsid FROM weights;"
        if self.var_type == 'VarID':
            sql_statement = "SELECT distinct gene,VarID FROM weights;"
        sql_cur.execute(sql_statement)
        var_table = sql_cur.fetchall()
        sql_cur.close()
        sql_con.close()
        data = {}
        for var_entry in var_table:
            gene = var_entry[0]
            variant_id = var_entry[1]
            if gene not in data.keys():
                data[gene] = set()
            data[gene].add(variant_id)
            self.variants.add(variant_id)
        return data
    

    def check_format(self, dataset_id:str, row:dict) -> None:
        ''' Check that the file columns match the expected covariance columns. '''
        file_columns = sorted(row.keys())
        if file_columns != list(self.covariance_columns):
            print(f'  >> Covariance file having different columns for {dataset_id}:')
            print(f'  >> -> File: {file_columns}')
            print(f'  >> -> Expected: {list(self.covariance_columns)}')
        self.dataset_format_checked.append(dataset_id)


    def validate_covariance_files(self) -> None:
        ''' Run the validation for each file/dataset. '''
        for dataset in self.datasets:
            dataset_id = dataset.id
            missing_genes = 0
            different_rsid1 = 0
            unknown_rsid2 = 0
            if dataset_id in self.sqlite_files.keys() and dataset_id in self.covariance_files.keys():
                print(f'# Dataset {dataset_id} ({dataset.name})')
                varid_list = self.fetch_varids(self.sqlite_files[dataset_id])
                varid_list_keys = varid_list.keys()
                with gzip.open(f'{self.covariance_dir}/{self.covariance_files[dataset_id]}', 'rt') as f:
                    reader = csv.DictReader(f, delimiter='\t')
                    for row in reader:
                        if dataset_id not in self.dataset_format_checked:
                            self.check_format(dataset_id, row)
                        gene = row['GENE']
                        rsid1 = row['RSID1']
                        rsid2 = row['RSID2']
                        # Checks
                        if gene in varid_list_keys:
                            vars = varid_list[gene]
                            # Check the variant is associated with the gene
                            if rsid1 not in vars:
                                different_rsid1 += 1
                            # Check that rsid2 is in the dataset
                            if rsid2 not in self.variants:
                                unknown_rsid2 += 1

                        else:
                            missing_genes += 1
                if missing_genes != 0:
                    print(f'  - missing_genes: {missing_genes}')
                if different_rsid1 != 0:
                    print(f'  - different_rsid1: {different_rsid1}')
                if unknown_rsid2 != 0:
                    print(f'  - unknown_rsid2: {unknown_rsid2}')
                if not missing_genes and not different_rsid1 and not unknown_rsid2:
                    print(f'  > No missing data')

            elif dataset_id in self.sqlite_files.keys():
                print(f'  >> Covariance file missing for {dataset_id}')
            elif dataset_id in self.covariance_files.keys():
                print(f'  >> SQLite file missing for {dataset_id}')
            else:
                print(f'  >> SQLite and Covariance files missing for {dataset_id}')