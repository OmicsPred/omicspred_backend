from imports.omicspred.parsers.metadata import MetadataTemplate


def run():

    # file_loc = '/Users/lg10/Documents/OmicsPred/data/GTEx_V8_full_metadata.xlsx'
    file_loc = '/Users/lg10/Documents/OmicsPred/data/GTEx_V8_sample_metadata.xlsx'

    dataset_prefix = 'GTExV8'

    metadata_template = MetadataTemplate(file_loc)

    metadata_template.read_curation(dataset_prefix)
    metadata_template.import_curation()