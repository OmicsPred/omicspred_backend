import os
from django.db.models import Q
from omicspred.models import *
from exports.config import scoring_file_from_file_config



def read_file_content(filepath:str) -> str:
    with open(filepath) as f:
        return f.read()


def generate_scoring_file_header(score:Score, dataset:Dataset):
    ''' Generate a scoring file header '''
    publication_model = dataset.publication
    reported_trait = ''
    if score.trait_reported and score.trait_reported_id:
        reported_trait = f'{score.trait_reported} ({score.trait_reported_id})'
    elif score.trait_reported:
            reported_trait = score.trait_reported
    else:
        reported_trait = score.trait_reported_id
    return f'''#omicspred_id={score.id}
#pgs_name={score.name}
#trait_type=proteomics
#measurement_tissue={dataset.tissue.label} ({dataset.tissue.id})
#measurement_platform=Somalogic ({dataset.platform.version})
#trait_reported={reported_trait}
#genome_build={score.variants_genomebuild}
#variants_number={score.variants_number}
#citation={publication_model.firstauthor} et al. {publication_model.journal} ({publication_model.pub_year}). doi:{publication_model.doi}
#license={score.license}'''


def write_scoring_file(header:str, content:str, filepath:str) -> None:
    ''' Write new scoring file with header '''
    with open(filepath, 'w') as output_file:
        output_file.write('\n'.join(header))
        output_file.write(f'{header}\n')
        output_file.write(content)


def check_dir_exist(dirpath:str):
    if not os.path.isdir(dirpath):
        try:
            os.mkdir(dirpath)
        except OSError as e:
            print("Error:", e)
            exit()


def get_dataset_label(id:str, name:str) -> str:
    dataset_label = f'{id}_{name}'
    dataset_label = dataset_label.replace(' - ','_').replace(' ','_')
    return dataset_label


def run():

    pmid = scoring_file_from_file_config['pmid']
    input_dir_root = scoring_file_from_file_config['input_dir_root']
    output_dir_root = scoring_file_from_file_config['output_dir_root']

    check_dir_exist(output_dir_root)

    input_dirs = {}
    for scores_dir in os.listdir(input_dir_root):
        scores_dir_path = f'{input_dir_root}/{scores_dir}'
        if os.path.isdir(scores_dir_path):
            print(f'-> input_dir_name > {scores_dir}: {scores_dir_path}')
            input_dirs[scores_dir] = scores_dir_path

    datasets = Dataset.objects.filter(publication__pmid=pmid)

    for dataset in datasets:
        print(f"# {dataset.name} ({dataset.id}) - {dataset.num}")
        dataset_id = dataset.id
        dataset_name = dataset.name
        dataset_label = get_dataset_label(dataset_id,dataset_name)
        dir_to_process = None
        output_dir = f'{output_dir_root}/{dataset_label}'
        check_dir_exist(output_dir)
        score_source_input_dir_name = ''
        for input_dir_name in input_dirs:
            if input_dir_name in dataset_name or input_dir_name in dataset_id:
                print(f"DIR FOUND: {input_dir_name} | {dataset_name} | {dataset_id}")
                dir_to_process = input_dirs[input_dir_name]
                score_source_input_dir_name = input_dir_name
        if not dir_to_process:
            print(f">>> Can't find a directory matching the dataset '{dataset_name}' (dataset_id)")
            exit()
        matching_score = 0
        for file in os.listdir(dir_to_process):
            filepath = f'{dir_to_process}/{file}'
            if os.path.isfile(filepath) and file.endswith('.txt'):
                # print(f" - {filepath}")
                score_name = file.replace('.txt','')
                # Specific code for ARIC
                if 'ARIC' in dataset.name:
                   anc = os.path.split(score_source_input_dir_name)[1]
                   score_name += f'_{anc}'  
                try:
                    score = Score.objects.get(Q(name__iexact=score_name) & Q(dataset_id=dataset.num))
                    output_file = f'{output_dir}/{score.id}.txt' 
                    file_header = generate_scoring_file_header(score,dataset)
                    file_content = read_file_content(filepath)
                    write_scoring_file(file_header, file_content, output_file)
                    matching_score += 1
                except Score.DoesNotExist:
                    print(f"Can't find a score matching the filename '{file}' ({filepath})")
            else:
                print(f"Can't find the file '{filepath}'")
        print(f">> DATASET {dataset_id}: {matching_score}/{dataset.scores_count} scores")



    