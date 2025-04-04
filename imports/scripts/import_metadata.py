from imports.omicspred.parsers.metadata import MetadataTemplate


def run():

    # file_loc = '/Users/lg10/Documents/OmicsPred/data/GTEx_V8_full_metadata.xlsx'
    file_loc = '/Users/lg10/Documents/OmicsPred/data/GTEx_V8_sample_metadata.xlsx'

    dataset_prefix = 'GTExV8'

    license = 'Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)'

    metadata_template = MetadataTemplate(file_loc,license)

    metadata_template.read_curation(dataset_prefix)
    metadata_template.import_curation()