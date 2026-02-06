from datetime import date
from omicspred.models import *
from exports.metadata_build_export import MetadataExport
from exports.config import metadata_exports_dir


def run():

    # datasets = Dataset.objects.all().order_by('num')
    datasets = Dataset.objects.filter(num=1).order_by('num')
    print("## Start metadata exports, dataset by dataset")
    datasets_total = len(datasets)
    count_dataset = 0
    for dataset in datasets:
        count_dataset += 1
        dataset_id = dataset.id
        print(f"- Dataset {dataset_id} ({count_dataset}/{datasets_total})")
        
        # Prepare data for exports
        metadata2export = MetadataExport(metadata_exports_dir,dataset)
        metadata2export.generate_metadata()