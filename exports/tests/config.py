import os

current_dir = os.getcwd()
metadata_exports_publication_id = 1
metadata_exports_dir = current_dir+'/exports/tests/output'
phewas_exports_dir = current_dir+'/exports/tests/output'
sqlite_exports_dir = current_dir+'/exports/tests/data/'


sqlite_default_values = {
    'opp_id': 'OPP000001',
    'sqlite_dir': current_dir+'/exports/tests/output/',
    'scoring_files_dir': current_dir+'/exports/tests/data/scoring_files',
    'use_different_id_as_gene': 'opgs_id'
}