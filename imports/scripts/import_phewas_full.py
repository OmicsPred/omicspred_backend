import csv
from imports.applications.parsers.phecode import *
from imports.applications.models.phecode import PhecodeData
from imports.applications.models.cohort import CohortData
from imports.applications.models.platform import PlatformData
from imports.applications.models.score import ScoreData
from imports.applications.models.sample import SampleData
from applications.models import Phecode

path_root = '/Users/lg10/Workspace/git/clone/OmicsPred_bak/src/pages/Applications/data'
phecode_full_asso_path = f'{path_root}/phecode.txt'


applications_db = 'applications'

platform_mapping = {
    'SomaScan': 'Somalogic',
    'RNAseq': 'Illumina RNAseq',
}

def fetch_data(filepath):
    data = []
    with open(phecode_full_asso_path, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        next(reader, None)  # skip the headers
        for row in reader:
            platform = row[6]
            if platform in platform_mapping.keys():
                platform = platform_mapping[platform]
            entry = {
                'PheCode': row[0],
                'Phenotype': row[1],
                'Category': row[2],
                'OMICSPRED ID': row[4],
                'Internal R2': row[5],
                'Platform': platform,
                'Hazard Ratio': row[8],
                'FDR adjusted P-value': row[9]
            }
            data.append(entry)
    return data


def parse_full_structured_content():
    ''' Parse full PheWAS data '''
    full_structured_content = fetch_data(phecode_full_asso_path)
    print("- Parsed full_structured_content")

    for data_info in full_structured_content:
        data_info
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


# def post_process_phecode():
#     root_phecode = Phecode.objects.using(applications_db).filter(id__iregex=r'^\d+$')
#     for r_phecode in root_phecode:
#         phecode_id = r_phecode.id
#         print(f"# {phecode_id}")
#         child_phecode = Phecode.objects.using(applications_db).filter(id__iregex=r'^'+phecode_id+'\.\d+$')
#         if child_phecode:
#             for c_phecode in child_phecode:
#                 print(f"  - {c_phecode.id}: {c_phecode.name}")
#                 r_phecode.child_phecode.add(c_phecode)
#             r_phecode.save(using=applications_db)


def run():
    # # Parse full PheWAS data
    parse_full_structured_content()

    # Phecode parent/child updates
    # post_process_phecode()
