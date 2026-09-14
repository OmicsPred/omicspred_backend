from omicspred.models import *


def run():

    data = {}
    data_keys = set()
    print("## Fetch Datasets ##")
    # Takes few minutes to run the datasets querysets but it makes the rest of the script faster
    datasets = Dataset.objects.select_related('platform','tissue').all().prefetch_related('dataset_score','dataset_score__genes','dataset_score__proteins','dataset_score__metabolites').order_by('num')
    total_datasets = len(datasets)
    count_dataset = 0
    for dataset in datasets:
        count_dataset += 1
        print(f"# Dataset {dataset.id} ({count_dataset}/{total_datasets})")
        omics_type = dataset.omics_type
        tissue_id = dataset.tissue.id
        platform_id = dataset.platform.id
        scores = dataset.dataset_score
        count_scores = 0
        total_scores = dataset.scores_count
        for score in scores.all():
            mt_list = []
            if omics_type == "gene expression":
                mt_list = score.genes.all()
            elif omics_type == "protein":
                genes_ids = set()
                for pr in score.proteins.all():
                    if pr.gene:
                        gene = pr.gene
                        gene_id = gene.external_id if gene.external_id else gene.name
                        if gene_id not in genes_ids:
                            mt_list.append(gene)
                            genes_ids.add(gene_id)
                    else:
                        mt_list.append(pr)
            elif omics_type == "metabolite":
                mt_list = score.metabolites.all()
            if len(mt_list) == 0:
                print(f"- No molecular trait found for score {score.id}")

            # If a score is mapped to more than 1 molecular trait, each molecular trait will be used as a distinct trait
            for mt in mt_list:
                molecular_trait = mt.external_id if mt.external_id else mt.name
                if molecular_trait and molecular_trait != '':
                    unique_trait_id = f'{molecular_trait}_{tissue_id}_{platform_id}'
                    if unique_trait_id in data_keys:
                        data[unique_trait_id] += 1
                    else:
                        data[unique_trait_id] = 1
                        data_keys.add(unique_trait_id)
                    
                else:
                    print(f'- Missing molecular trait name/ID for score {score.id}')
               
            count_scores += 1
            if str(count_scores).endswith('00000'):
                print(f'  - {count_scores}/{total_scores} scores processed')
        print(f'  - {count_scores}/{total_scores} scores processed')
    print(f"\n=> Total unique traits: {len(data.keys())}")

    print(f">> Write into file ...")
    filename = 'unique_traits.txt'
    try:
        with open(filename, 'w') as f:
            try:
                f.write('trait\toccurences')
                for trait in data.keys():
                    f.write(f'\n{trait}\t{data[trait]}')
                print(f">> File {filename} generated")
            except (IOError, OSError):
                print(f"!! Error writing to file {filename}")
    except (FileNotFoundError, PermissionError, OSError):
        print(f"!! Error opening file {filename}")
