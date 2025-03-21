import re
from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from omicspred.models import Sample

class SampleData(GenericData):

    def __init__(self, sample_data:dict):
        GenericData.__init__(self)
        for item in sample_data.keys():
            if sample_data[item]:
                 self.data[item] = sample_data[item]


    def check_sample_model_exist(self):
        '''
        Check if a Sample model already exists.
        Only to be used for GWAS/Dev samples from existing Scores in the database!
        Return type: Sample object (omicspred.models) or None
        '''
        sample_data = {}
        s_cohorts = ''
        for field, val in self.data.items():
            if field == 'cohorts':
                # s_cohorts = self.data['cohorts'].name_short
                s_cohorts = '|'.join(sorted([x.name_short for x in self.data['cohorts']]))
            else:
                sample_data[field] = val

        samples = Sample.objects.filter(**sample_data).order_by('id')

        if len(samples) != 0:
            for sample in samples:
                cohorts = '|'.join(sorted([x.name_short for x in sample.cohorts.all()]))
                if s_cohorts == cohorts:
                    return sample
        return None


    @transaction.atomic
    def create_model(self):
        '''
        Create an instance of the Sample model.
        It also create instance(s) of the Demographic model (sample_age, followup_time) if needed.
        Return type: Sample model
        '''
        try:
            with transaction.atomic():
                self.model = self.check_sample_model_exist()
                if not self.model:
                    self.model = Sample()
                    cohorts = []
                    for field, val in self.data.items():
                        if field == 'cohorts':
                            # Stored as list of CohortData -> Cohort Model
                            for cohort_data in val:
                                cohort = cohort_data.create_model()
                                cohorts.append(cohort)
                            continue
                        elif field in ['ancestry_broad','ancestry_country','ancestry_free']:
                            # Add space after each comma (for consistency & comparison)
                            val = re.sub(r'(?<=[,])(?=[^\s])', r' ', val)
                            if field == 'ancestry_broad' and (val == '' or val == 'NR'):
                                val = 'Not reported'
                        elif field == 'sample_percent_male':
                            # Remove % character
                            val_str = str(val)
                            if re.search('\%',val_str):
                                val_str = re.sub(r'\%', r'', val_str)
                                val_str = re.sub(r' ', r'', val_str)
                                val = float(val_str)
                        setattr(self.model, field, val)
                    self.model.save()
                    # Add cohort(s)
                    for cohort in cohorts:
                        self.model.cohorts.add(cohort)

                    # Add ancestry broad data if none exists
                    if self.model.ancestry_broad == '' or not self.model.ancestry_broad:
                        self.model.ancestry_broad = 'Not reported'

                    # Need to create the Sample object first (with an ID)
                    self.model.cohorts.set(cohorts)

                    # Save updates
                    self.model.save()
        except IntegrityError as e:
            self.model = None
            print(f'Error with the creation of the Sample(s) and/or the Demographic(s) and/or the Cohort(s): {e}')

        return self.model
