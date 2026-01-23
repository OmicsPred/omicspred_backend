import datetime
from imports.omicspred.parsers.metadata import MetadataTemplate
from imports.config import *

def run():

    # file_loc = '/Users/lg10/Documents/OmicsPred/metadata/GTEx_V8_full_metadata.xlsx'
    # file_loc = '/Users/lg10/Documents/OmicsPred/metadata/PredictDB/full_metadata_enet_sqtl_updated_to_import.xlsx'
    # file_loc = '/Users/lg10/Documents/OmicsPred/metadata/PredictDB/full_metadata_mashr_eqtl_updated_to_import.xlsx'
    # file_loc = '/Users/lg10/Documents/OmicsPred/metadata/PredictDB/full_metadata_mashr_sqtl_1_updated_to_import.xlsx'
    # file_loc = '/Users/lg10/Documents/OmicsPred/metadata/PredictDB/full_metadata_mashr_sqtl_2_updated_to_import.xlsx'
    # file_loc = '/Users/lg10/Documents/OmicsPred/metadata/ARIC/ARIC_metadata.xlsx'

    # dataset_prefix = 'ARIC - '

    # license = 'Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)'

    # Use data from the config file
    metadata_template = MetadataTemplate(file_loc,omics_type,license,species)

    start_time = datetime.datetime.now()

    print(f"Start time: {start_time}")
    metadata_template.read_curation(dataset_prefix)
    metadata_template.import_curation()

    end_time = datetime.datetime.now()

    print(f"Started time: {start_time}")
    print(f"Ended time: {end_time}")