
# Metadata exports
metadata_exports_dir = '<path_to_directory>'


# SQLite exports
sqlite_default_values = {
    'opp_id': '<dataset_id>', # e.g. OPP000003
    'sqlite_dir': '<path_to_directory_to_store_sqlite_files>',
    'scoring_files_dir': '<path_to_scoring_files_dataset_directory>', # Uncompressed dataset directory 
    'method_name': '<dataset_method_name>',  # Only needed for GTEx exports
    'platform_name': '<platform_name>',      # Only needed for GTEx exports
    'use_opgs_id_as_gene': '<True_or_False>' # Use the OmicsPred ID in the 'gene' column or not
}


# Scoring files exports - only for PredictDB studies
scoring_file_config = {
    'pmid': '<pubmed ID>', # e.g. 32913098
    'variant_coords_sqlite_db_file': '<path_to_variant_coords_knowledge_base>', # Will be created if it doesn't exist yet
    'dbs_location': '<path_to_sqlite_directory>',
    'scores_root_dir': '<path_to_directory_to_store_the_scoring_files',
    'sqlite_file_prefix': '<sqlite_file_prefix>', # e.g. 'mashr_'
    'sqlite_file_suffix': '<sqlite_file_suffix>', # e.g. '_model'
    'ds_name': '<dataset_name_or_part_of_its_name>' # e.g. '- sQTL - MASHR -'
}