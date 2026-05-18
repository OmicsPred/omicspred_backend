from omicspred.models import Dataset
from exports.phewas_export import PheWASExport
from exports.datasets import DatasetsSelection
from exports.config import phewas_exports_dir


# Need to run first the script import/phewas/add_mappings (and store the SQLite file in <raw_file_dir>/metadata)

def run():
    # Fetch dataset(s)
    ds_selection = DatasetsSelection()
    datasets = ds_selection.get_datasets()

    print("## Start PheWAS exports, dataset by dataset")
    datasets_total = len(datasets)
    count_dataset = 0
    for dataset in datasets:
        count_dataset += 1
        dataset_id = dataset.id
        print(f"\n## Dataset {dataset_id} ({count_dataset}/{datasets_total}) - {dataset.phewas_count:,} PheWAS ##")
        phewas_export_file = f'{dataset.id}_phewas.txt'
        
        # Prepare data for exports - only DB
        phewas_export = PheWASExport(phewas_export_file, phewas_exports_dir, dataset)
        
        phewas_export.generate_export()