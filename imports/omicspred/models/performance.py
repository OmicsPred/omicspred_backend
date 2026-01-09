import numpy as np
from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from imports.omicspred.models.metric import MetricData
from omicspred.models import Dataset,Performance,Sample,Score

class PerformanceData(GenericData):

    # ancestries = {
    #     'Additional Asian Ancestries': 'MA',
    #     'African American or Afro-Caribbean': 'AFA',
    #     'African American or Afro-Caribbean, East Asian, European, Hispanic or Latin American': 'ALL',
    #     'East Asian': 'CHN', #'CN'
    #     'European': 'EUR',
    #     'Hispanic or Latin American': 'HIS',
    #     'South Asian': 'IN',
    # }
    ancestries = {
        'Ad Mixed American': 'AMR',
        'African': 'AFR',
        'African American or Afro-Caribbean': 'AFR',
        'East Asian': 'EAS',
        'European': 'EUR',
        'European,Ad Mixed American,African,East Asian,South Asian': 'ALL',
        'African American or Afro-Caribbean, East Asian, European, Hispanic or Latin American': 'ALL',
        'Hispanic or Latin American': 'AMR',
        'South Asian': 'SAS'
    }


    def __init__(self):
        GenericData.__init__(self)
        self.metrics = []


    def add_eval_type(self, eval_type:str):
        self.data['eval_type'] = eval_type


    def add_score_model(self, score_model:Score):
        self.data['score'] = score_model


    def add_sample_model(self, sample_model:Sample):
        self.data['sample'] = sample_model
        self.data['cohort_label'] = self.get_cohort_label(sample_model)


    def add_dataset_model(self, dataset_model:Dataset):
        self.data['dataset'] = dataset_model


    def add_metrics(self,metrics_data):
        '''
        Method adding MetricData objects to the metrics array.
        '''
        self.metrics.append(metrics_data)
        # for metric_type in metric_values.keys():
        #     metric_val = None
        #     pvalue_val = None
        #     if 'pvalue' not in metric_type:
        #         pval_col = f'{metric_type}_pvalue'
        #         if pval_col in metric_values.keys():
        #             if metric_values[pval_col] not in [None,np.nan,'nan','']:
        #                 pvalue_val = metric_values[pval_col]
        #         if metric_values[metric_type] not in [None,np.nan,'nan','']:
        #             metric_val = metric_values[metric_type]
        #         if metric_val != None:
        #             metric_data = MetricData(metric_type,metric_val,pvalue_val)
        #             self.metrics.append(metric_data)


    def get_cohort_label(self, sample_model:Sample) -> str:
        cohorts = [x.name_short for x in sample_model.cohorts.all()]
        cohort_label = '_'.join(sorted(cohorts))
        # if cohort_label in ['MEC','MESA','UKB_Withheld']:
        if cohort_label in ['MEC','UKB_Withheld']:
            sample_anc = sample_model.ancestry_broad
            if sample_anc in self.ancestries.keys():
                cohort_label = f'{cohort_label}_{self.ancestries[sample_anc]}'
        return cohort_label


    def update_eval_type(self):
        eval_type = self.data['eval_type']
        eval_type_choices = Performance.eval_type.field.choices
        eval_types =  {}
        for choice in eval_type_choices:
            eval_types[choice[1]] = choice[0]
        if eval_type in eval_types.keys():
            self.data['eval_type'] = eval_types[eval_type]


    @transaction.atomic
    def create_model(self):
        '''
        Create an instance of the Performance model.
        Return type: Performance model
        '''
        try:
            with transaction.atomic():
                # self.update_eval_type()
                self.model = Performance(**self.data)
                self.model.save()

            # Create associated Metric objects
            for metric in self.metrics:
                metric_model = metric.create_model(self.model)

        except IntegrityError as e:
            self.model = None
            print(f'Error with the creation of the Performance(s) and/or the Metric(s): {e}')

        return self.model
