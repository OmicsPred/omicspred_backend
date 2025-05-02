import datetime
from imports.omicspred.parsers.metadata import MetadataTemplate


def run():

    file_loc = '/Users/lg10/Documents/OmicsPred/metadata/GTEx_V8_full_metadata.xlsx'
    # file_loc = '/Users/lg10/Documents/OmicsPred/metadata/GTEx_V8_sample_metadata.xlsx'

    dataset_prefix = 'GTExV8'

    license = 'Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)'

    metadata_template = MetadataTemplate(file_loc,license)

    start_time = datetime.now()

    print(f"Start time: {start_time}")
    metadata_template.read_curation(dataset_prefix)
    metadata_template.import_curation()

    end_time = datetime.now()

    print(f"Started time: {start_time}")
    print(f"Ended time: {end_time}")