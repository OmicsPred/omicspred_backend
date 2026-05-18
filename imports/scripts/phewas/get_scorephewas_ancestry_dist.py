import re
from omicspred.models import *


anc_mapping = {
    'Ad Mixed American': 'AMR', # <- to be confirmed (could be African American)
    'Additional Asian Ancestries': 'ASN',
    'Additional Diverse Ancestries': 'OTH',
    'African': 'AFR',
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

def run():
    count = 1
    scores_phewas = ScorePheWAS.objects.filter(dataset_id=209).prefetch_related('samples').distinct()
    # scores_phewas = ScorePheWAS.objects.all().prefetch_related('samples').distinct()
    # scores = Score.objects.all().prefetch_related('score_performance','score_performance__sample')
    multi_anc = 'MAO'

    # debug_count = 0
    scores_count = len(scores_phewas)
    print_interval = '000' if scores_count < 10000 else '0000'
    print(f"Scores to update: {scores_count}")
    for score in scores_phewas:

        # Init variables
        sample_dist = { 'anc':{}, 'count':0 }

        for sample in score.samples.all():
            sample_number = sample.sample_number
            ancestry = sample.ancestry_broad
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
        
        # Calculate training sample percentage
        count_total_samples = sample_dist['count']
        for anc in sample_dist['anc'].keys():
            anc_count = sample_dist['anc'][anc]['count']
            # Calculate percentage
            if count_total_samples == 0:
                anc_number = len(sample_dist['anc'].keys())
                percent = (1/anc_number)*100
            else:
                percent = (anc_count/count_total_samples)*100

            # Format percentage
            percent = format_percentage(percent)

            sample_dist['anc'][anc]['dist'] = percent

        count += 1
        if str(count).endswith(print_interval):
            print(f'# {count} scores processed')

        try:
            if sample_dist:
                score.ancestry = sample_dist
                score.save()
            else:
                print(f"  --> {score.score_id}: no anc")
        except Exception as e:
            print(f"--> Error with {score.score_id}: {e}")
            exit(1)

    print(f'# {count} scores PheWAS processed')