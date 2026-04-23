from omicspred.models import Dataset
from exports.phewas_export import PheWASExport
from exports.config import phewas_exports_dir
# from django.db.models import Q


# Need to run first the script import/phewas/add_mappings (and store the SQLite file in <raw_file_dir>/metadata)

def run():
    # datasets = Dataset.objects.filter(Q(publication_id=metadata_exports_publication_id) & Q(name__icontains='sQTL - Enet')).order_by('num')
    # datasets = Dataset.objects.filter(Q(publication_id=metadata_exports_publication_id) & Q(num__lte=56)).order_by('num')
    # datasets = Dataset.objects.filter(publication_id=metadata_exports_publication_id).order_by('num')
    # datasets = Dataset.objects.all().order_by('num')
    # datasets = Dataset.objects.filter(publication_id=1).order_by('num')
    # datasets = Dataset.objects.filter(id__in=['OPD000006','OPD000056','OPD000105','OPD000154','OPD000203'])
    datasets = Dataset.objects.filter(id__in=['OPD000204','OPD000205','OPD000208','OPD000209','OPD000210','OPD000211','OPD000212','OPD000213'])
    # datasets = Dataset.objects.filter(num=203).order_by('num')
    print("## Start PheWAS exports, dataset by dataset")
    datasets_total = len(datasets)
    count_dataset = 0
    for dataset in datasets:
        count_dataset += 1
        dataset_id = dataset.id
        print(f"- Dataset {dataset_id} ({count_dataset}/{datasets_total}) - {dataset.phewas_count:,} PheWAS")
        phewas_export_file = f'{dataset.id}_phewas.txt'
        
        # Prepare data for exports - only DB
        phewas_export = PheWASExport(phewas_export_file, phewas_exports_dir, dataset)

        # Prepare data for exports - DB + file
        # raw_file_dir = '/Users/lg10/Workspace/datafiles/OmicsPred/phenotypes'
        # phewas_export = PheWASExport(phewas_export_file, phewas_exports_dir, dataset, raw_file_dir)
        
        phewas_export.generate_export()