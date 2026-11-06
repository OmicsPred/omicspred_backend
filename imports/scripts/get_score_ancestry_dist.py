import re
from omicspred.models import *


anc_mapping = {
    'Ad Mixed American': 'AMR', # <- to be confirmed (could be African American)
    'Additional Asian Ancestries': 'ASN',
    'Additional Diverse Ancestries': 'OTH',
    'African': 'AFR',
    'African unspecified': 'AFR',
    'African American': 'AFR',
    'African American or Afro-Caribbean': 'AFR',
    'Asian unspecified': 'ASN',
    'East Asian' : 'EAS',
    'European': 'EUR',
    'Greater Middle Eastern': 'GME',
    'Hispanic or Latin American': 'AMR',
    'Not Reported': 'NR',
    'Other': 'OTH',
    'South Asian': 'SAS',
    'Multi-ancestry': 'MAO' # <- to be replaced
}

multi_anc = 'MAO'
debug_count_max = 10

def format_percentage(percent):
    # Round and remove extra 0 for percentage
    if percent < 0.1:
        percent = "{:.2f}".format(percent)
        percent = percent.replace('.00','')
    else:
        percent = "{:.1f}".format(percent)
        percent = percent.replace('.0','')

    # Convert percentage type to float or int
    if re.match(r'^\d+\.\d+$', percent):
        percent = float(percent)
    else:
        percent = int(percent)
    return percent


def build_ancestry_dist(ancestry:str, sample_number:int, sample_dist:dict) -> dict:
    if ',' in ancestry:
        anc_labels = set()
        for anc in ancestry.split(','):
            anc = anc.strip()
            if not anc in anc_mapping.keys():
                raise Exception(f"Error: ancestry {anc} not found in authorised list of ancestries")
            anc_label = anc_mapping[anc]
            anc_labels.add(anc_label)
        if multi_anc in sample_dist['anc'].keys():
            multi_anc_list = set(sample_dist['anc'][multi_anc]['anc_list'])
            for anc_label in anc_labels:
                multi_anc_list.add(anc_label)
            sample_dist['anc'][multi_anc]['anc_list'] = list(multi_anc_list)
            sample_dist['anc'][multi_anc]['count'] += sample_number
        else:
            sample_dist['anc'][multi_anc] = {'count': sample_number, 'anc_list': list(anc_labels)}
    # Single ancestry
    else:
        if not ancestry in anc_mapping.keys():
            raise Exception(f"Error: ancestry {ancestry} not found in authorised list of ancestries")
        anc_label = anc_mapping[ancestry]
        if anc_label in sample_dist['anc'].keys():
            sample_dist['anc'][anc_label]['count'] += sample_number
        else:
            sample_dist['anc'][anc_label] = {'count': sample_number}
    sample_dist['count'] += sample_number

    return sample_dist


def calculate_ancestry_percentage(sample_dist:dict) -> dict:
    count_total_tr = sample_dist['count']
    for anc in sample_dist['anc'].keys():
        anc_count = sample_dist['anc'][anc]['count']
        # Calculate percentage
        if count_total_tr == 0:
            anc_number = len(sample_dist['anc'].keys())
            percent = (1/anc_number)*100
        else:
            percent = (anc_count/count_total_tr)*100

        # Format percentage
        percent = format_percentage(percent)

        sample_dist['anc'][anc]['dist'] = percent
    return sample_dist


def get_score_ancestry_dist():
    count = 1
    scores = Score.objects.filter(dataset__num__gte=217).prefetch_related('score_performance','score_performance__sample').distinct()
    # scores = Score.objects.all().prefetch_related('score_performance','score_performance__sample')

    # debug_count = 0
    scores_count = len(scores)
    print_interval = '000' if scores_count < 10000 else '0000'
    print(f"Scores to update: {scores_count}")
    for score in scores:

        # Init variables
        sample_training_dist = { 'anc':{}, 'count':0 }
        sample_validation_dist = { 'anc':{}, 'count':0 }

        for performance in score.score_performance.all():
            sample = performance.sample
            sample_number = sample.sample_number
            ancestry = sample.ancestry_broad
            type = 'Training' if performance.eval_type in ['T', 'Training'] else 'Validation'

            # Training sample
            if type == 'Training':
                sample_training_dist = build_ancestry_dist(ancestry, sample_number, sample_training_dist)

            # Validation sample
            if type == 'Validation':
                sample_validation_dist = build_ancestry_dist(ancestry, sample_number, sample_validation_dist)

        # Calculate training sample percentage
        sample_training_dist = calculate_ancestry_percentage(sample_training_dist)

        # Calculate validation sample percentage
        sample_validation_dist = calculate_ancestry_percentage(sample_validation_dist)

        count += 1
        if str(count).endswith(print_interval):
            print(f'# {count} scores processed')

        json_content = {}
        if sample_training_dist['anc']:
            json_content['dev'] = sample_training_dist
        if sample_validation_dist['anc']:
            json_content['eval'] = sample_validation_dist

        try:
            if json_content:
                score.ancestry = json_content
                score.save()
            else:
                print(f"  --> {score.id}: no anc")
        except Exception as e:
            print(f"--> Error with {score.id}: {e}")
            exit(1)

    print(f'# {count} scores processed')


def get_dataset_ancestry_dist():
    # count = 1
    datasets = Dataset.objects.all().order_by('num')
    # datasets = Dataset.objects.filter(num__lte=5).order_by('num')

    for dataset in datasets:
        print(f'# Dataset {dataset.id}')
        # Training samples
        sample_training_dist = {'anc':{},'count':0}
        samples_training = dataset.samples_training.all()
        for sample in samples_training:
            ancestry = sample.ancestry_broad
            sample_number = sample.sample_number
            sample_training_dist = build_ancestry_dist(ancestry, sample_number, sample_training_dist)
        # Calculate average count for multi-samples
        if len(samples_training) > 1:
            sample_training_dist['avg_count'] = int(round(sample_training_dist['count']/len(samples_training),0))

        # Validation samples
        sample_validation_dist = {'anc':{},'count':0}
        samples_validation = dataset.samples_validation.all()
        for sample in samples_validation:
            ancestry = sample.ancestry_broad
            sample_number = sample.sample_number
            sample_validation_dist = build_ancestry_dist(ancestry, sample_number, sample_validation_dist)
        # Calculate average count for multi-samples
        if len(samples_validation) > 1:
            sample_validation_dist['avg_count'] = int(round(sample_validation_dist['count']/len(samples_validation),0))

        # Calculate training sample percentage
        sample_training_dist = calculate_ancestry_percentage(sample_training_dist)

        # Calculate validation sample percentage
        sample_validation_dist = calculate_ancestry_percentage(sample_validation_dist)

        json_content = {}
        if sample_training_dist['anc']:
            json_content['dev'] = sample_training_dist
        if sample_validation_dist['anc']:
            json_content['eval'] = sample_validation_dist

        try:
            if json_content:
                dataset.ancestry = json_content
                dataset.save()
            else:
                print(f"  --> {dataset.id}: no anc")
        except Exception as e:
            print(f"--> Error with {dataset.id}: {e}")
            exit(1)

        print(f"  > {json_content}")

def run():
    get_score_ancestry_dist()
    get_dataset_ancestry_dist()