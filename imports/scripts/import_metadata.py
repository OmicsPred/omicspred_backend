import datetime
from imports.omicspred.parsers.metadata import MetadataTemplate
from imports.config import *

def run():

    # Use data from the config file
    metadata_template = MetadataTemplate(file_loc,platform_types,license,species)

    start_time = datetime.datetime.now()

    print(f"Start time: {start_time}")
    metadata_template.read_curation(dataset_prefix)
    metadata_template.import_curation()

    end_time = datetime.datetime.now()

    print(f"Started time: {start_time}")
    print(f"Ended time: {end_time}")