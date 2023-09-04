import json
from imports.omicspred.models.cohort import CohortData
from imports.omicspred.models.sample import SampleData



class SummaryParser():

    def __init__(self, summary_info:dict, extra_info:dict):
        self.study = summary_info['name']
        self.filepath = summary_info['filepath']
        self.extra_sample_info = extra_info
        self.validation = []
        self.samples = []


    def parse_summary_file(self):
        # Opening JSON file and load as dictionary
        f = open(self.filepath, 'r')
        print(f'FILE: {self.filepath}')
        content = json.load(f)
        f.close()

        for entry in content:
            if entry['title'].startswith('Number'):
                self.count = entry['value']
            elif entry['title'].startswith('Training cohort'):
                self.cohort = entry['value']
                if self.cohort == 'INTERVAL':
                    self.ancestry = 'European'
                else:
                    self.ancestry = 'Not Reported'
                if 'link' in entry.keys():
                    self.cohort_url = entry['link']
            elif entry['title'].startswith('Training sample size'):
                self.sample_count = entry['value']
            elif 'validation' in entry['title']:
                self.parse_validation(entry)

        training = {
            'type': 'training',
            'cohort': self.cohort,
            'count': self.count,
            'ancestry': f"{self.sample_count} {self.ancestry}"
        }
        if self.cohort_url:
            training['url'] = self.cohort_url

        self.validation.insert(0,training)

        print(f"# {self.study}")
        # for v in self.validation:
        #     print(f"  > Type: {v['type']} | Cohort {v['cohort']}")
        #     print(f"    Ancestry: {v['ancestry']} | Entities {v['count']}")


    def parse_validation(self, entry):
        validation = {}
        if entry['title'].startswith('Independent validation'):
            validation['type'] = 'independant'
        elif entry['title'].startswith('External validation'):
            validation['type'] = 'external'
        if 'link' in entry.keys():
            validation['url'] = entry['link']
        # Parse validation value
        v_content = entry['value'].split(' (')
        validation['cohort'] = v_content[0]
        v_details = v_content[1].replace(')','').split('; ')
        validation['ancestry'] = v_details[0]
        validation['count'] = v_details[1]
        self.validation.append(validation)


    def import_to_database(self):
        for v in self.validation:
            # Cohort
            if 'url' in v.keys():
                cohort_data = CohortData(v['cohort'],v['cohort'],v['url'])
            else:
                cohort_data = CohortData(v['cohort'],v['cohort'])
            cohort_model = cohort_data.create_model()
            cohort_name = v['cohort']

            # Sample
            sample_ancestries = v['ancestry'].split(', ')
            for sample_ancestry in sample_ancestries:
                cohort_label = None
                [sample_number, ancestry_broad] = sample_ancestry.split(' ',1)
                sample_number = int(sample_number.replace(',',''))
                for sample_cohort in self.extra_sample_info.keys():
                    if self.extra_sample_info[sample_cohort]['name'] == cohort_name and self.extra_sample_info[sample_cohort]['ancestry'] == ancestry_broad:
                        cohort_label = sample_cohort
                        break
                if cohort_label:
                    percent_male = self.extra_sample_info[cohort_label]['percent_male']
                    sample_age = self.extra_sample_info[cohort_label]['age']
                    sample_age_sd = self.extra_sample_info[cohort_label]['age_sd']
                    sample = SampleData(sample_number, ancestry_broad, cohort_model, percent_male, sample_age, sample_age_sd)
                else:
                    sample = SampleData(sample_number, ancestry_broad, cohort_model)
                sample_model_exist = sample.sample_model_exist()
                if not sample_model_exist:
                    sample_data = sample.create_model()

                else:
                    sample_data = sample_model_exist

                self.samples.append({ 'cohort': cohort_name, 'ancestry':ancestry_broad, 'sample': sample_data, 'entities_count': v['count'] })

        return self.samples
