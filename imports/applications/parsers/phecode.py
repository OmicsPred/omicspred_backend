import re
from psycopg.types.range import Range

class PhecodeFullParser():

    def __init__(self, data_info:dict):
        
        self.phecode = {
            'id': data_info['PheCode'],
            'name': data_info['Phenotype'],
            'category': data_info['Category']
        }
        self.score_application = {
            'score_id': data_info['OMICSPRED ID'],
            'r2': data_info['Internal R2'],
            'fdr': data_info['FDR adjusted P-value']
        }
        self.platform = {
            'name': data_info['Platform']
        }
        
        self.cohort = {
            'name_short': 'INTERVAL'
        }
        self.hazard_ratio = data_info['Hazard Ratio']


    def parse_hazard_ratio(self):
        values = self.hazard_ratio.split(' ')
        self.score_application['hr'] = values[0]
        if len(values) == 3:
            ci_low = values[1].replace('(','')
            ci_upper = values[2].replace(')','')
            self.score_application['hr_ci'] = Range(lower=float(ci_low), upper=float(ci_upper), bounds='[]')
    

    def fix_phecode_id(self):
        phecode_id = str(self.phecode['id'])
        new_phecode_id = re.sub('\.0$', '',phecode_id)
        self.phecode['id'] = new_phecode_id


    def parse_data(self):
        self.parse_hazard_ratio()
        self.fix_phecode_id()
        # print(self.score_application)




class PhecodeSumParser():

    def __init__(self, data_info:dict):
        
        self.phecode = {
            'id': data_info['Phecode'],
            'name': data_info['Phenotype'],
            'category': data_info['Category']
        }
        self.sample_application = {
            # 'sample_number': data_info['#Cases/#Samples'].split('/')[1],
            # 'sample_cases': data_info['#Cases/#Samples'].split('/')[0],
            'sample_percent_female': data_info['%Female'].replace('%',''),
            # 'sample_age': data_info['Mean Age'].split(' \u00b1 ')[0],
            # 'sample_age_sd': data_info['Mean Age'].split(' \u00b1 ')[1],
        }

        self.sample_count = data_info['#Cases/#Samples']
        self.sample_age = data_info['Mean Age']


    def parse_sample(self):
        # Sample count
        [cases,number] = self.sample_count.split('/')
        self.sample_application['sample_cases'] = cases
        self.sample_application['sample_number'] = number

        # Sample age
        [age,age_sd] = self.sample_age.split(' \u00b1 ')
        self.sample_application['sample_age'] = age
        self.sample_application['sample_age_sd'] = age_sd


    def fix_phecode_id(self):
        phecode_id = str(self.phecode['id'])
        new_phecode_id = re.sub('\.0$', '',phecode_id)
        self.phecode['id'] = new_phecode_id


    def parse_data(self):
        self.parse_sample()
        self.fix_phecode_id()
