import json
from imports.applications.parsers.phecode import *
from imports.applications.models.phecode import PhecodeData
from imports.applications.models.cohort import CohortData
from imports.applications.models.platform import PlatformData
from imports.applications.models.score import ScoreData
from imports.applications.models.sample import SampleData
from applications.models import Phecode

path_root = '/Users/lg10/Workspace/git/clone/OmicsPred_bak/src/pages/Applications/data'
phecode_full_asso_path = f'{path_root}/phecode.json'
phecode_sum_asso_path = f'{path_root}/all_omics_assoc_sum.json'


applications_db = 'applications'


def fetch_json_data(filepath):
    f = open(filepath, 'r')
    content = json.load(f)
    f.close()

    data = {}

    for entry in content:
        data_name = entry['name']
        data_content = entry['data']
        for id in data_content.keys():
            d_key = f'op_{id}'
            if not d_key in data.keys():
                data[d_key] = {}
            data[d_key][data_name] = data_content[id]
    return data


def parse_full_structured_content():
    ''' Parse full PheWAS data '''
    full_structured_content = fetch_json_data(phecode_full_asso_path)
    print("- Parsed full_structured_content")

    for id in full_structured_content.keys():
        data_info = full_structured_content[id]
        phecode = PhecodeFullParser(data_info)
        phecode.parse_data()
        # Phecode model
        phecode_data = PhecodeData(phecode.phecode)
        phecode_model = phecode_data.create_model()
        # Cohort model
        cohort_data = CohortData(phecode.cohort)
        cohort_model = cohort_data.create_model()
        # Platform model
        platform_data = PlatformData(phecode.platform)
        platform_model = platform_data.create_model()
        # ScoreApplication model
        score_app_data = ScoreData(phecode.score_application)
        score_app_data.add_data('phecode', phecode_model)
        score_app_data.add_data('cohort', cohort_model)
        score_app_data.add_data('platform', platform_model)
        score_app_model = score_app_data.create_model()
    print("- Imported full_structured_content")


def parse_sum_structured_content():
    ''' Parse summary PheWAS data '''
    sum_structured_content = fetch_json_data(phecode_sum_asso_path)
    print("- Parsed sum_structured_content")

    for id in sum_structured_content.keys():
        data_info = sum_structured_content[id]
        phecode = PhecodeSumParser(data_info)
        phecode.parse_data()
        # Phecode model
        phecode_data = PhecodeData(phecode.phecode)
        phecode_model = phecode_data.create_model()
        # SampleAppliction model
        sample_app_data = SampleData(phecode.sample_application)
        sample_app_data.add_data('phecode', phecode_model)
        sample_app_model = sample_app_data.create_model()
    print("- Imported sum_structured_content")


def post_process_phecode():
    root_phecode = Phecode.objects.using(applications_db).filter(id__iregex=r'^\d+$')
    for r_phecode in root_phecode:
        phecode_id = r_phecode.id
        print(f"# {phecode_id}")
        child_phecode = Phecode.objects.using(applications_db).filter(id__iregex=r'^'+phecode_id+'\.\d+$')
        if child_phecode:
            for c_phecode in child_phecode:
                print(f"  - {c_phecode.id}: {c_phecode.name}")
                r_phecode.child_phecode.add(c_phecode)
            r_phecode.save(using=applications_db)


def run():
    # # Parse full PheWAS data
    # parse_full_structured_content()

    # # Parse summary PheWAS data
    # parse_sum_structured_content()

    # Phecode parent/child updates
    post_process_phecode()
