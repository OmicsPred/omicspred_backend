from datetime import date
from omicspred.models import Dataset
from exports.metadata_build_export import MetadataExport
from exports.datasets import DatasetsSelection
from exports.config import metadata_exports_dir, sqlite_exports_dir


def run():
    # Fetch dataset(s)
    ds_selection = DatasetsSelection()
    datasets = ds_selection.get_datasets()

    print("## Start metadata exports, dataset by dataset")
    datasets_total = len(datasets)
    count_dataset = 0
    for dataset in datasets:
        count_dataset += 1
        dataset_id = dataset.id
        print(f"- Dataset {dataset_id} ({count_dataset}/{datasets_total})")
        
        # Prepare data for exports
        metadata2export = MetadataExport(metadata_exports_dir,sqlite_exports_dir, dataset)
        metadata2export.generate_metadata()