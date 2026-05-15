file_loc = '<path_to_metadata_spreadsheet_file>'

dataset_prefix = '<dataset_prefix_if_needed>'

license = 'Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)'

species = 'Homo sapiens'

platform_types = {
    'Olink': 'Proteomics',
    'Metabolon': 'Metabolomics',
    'Nightingale': 'Metabolomics',
    'RNAseq - Expression': 'Transcriptomics',
    'RNAseq - Splicing': 'Transcriptomics',
    'Somalogic': 'Proteomics',
}

# PhWAS imports
phewas_publication_id = '<publication_id>' # e.g. 1
phewas_method = '<method_description>' # e.g. S-PrediXcan
phewas_csv_dir = '<path_to_phewas_files_directory>'
efo_sqlite_filepath = '<path_to_efo_sqlite_db>' # cf. script 'create_efo_db.py'
