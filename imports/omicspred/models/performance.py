import numpy as np
from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from imports.omicspred.models.metric import MetricData
from omicspred.models import Performance,EFO

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
        'East Asian': 'EAS',
        'European': 'EUR',
        'European,Ad Mixed American,African,East Asian,South Asian': 'ALL',
        'South Asian': 'SAS'
    }

    def __init__(self,score,dataset,sample,efo,type,gwas_info,extra=None):
        GenericData.__init__(self)
        self.metrics = []
        # self.metric_models = []
        self.data = {
            'score': score,
            'dataset': dataset,
            'sample': sample,
            'eval_type': type
        }
        if efo:
           self.data['efo'] = efo
        self.get_cohort_label()
        if gwas_info:
            if 'gcst_id' in gwas_info.keys():
                self.data['source_gwas_catalog'] = gwas_info['gcst_id']
            if 'doi' in gwas_info.keys():
                self.data['source_doi'] = gwas_info['doi']
            if 'covariates' in gwas_info.keys():
                self.data['covariates'] = gwas_info['covariates']
        if extra:
            self.data['performance_additional'] = extra


    def add_metric(self,metric_values):
        '''
        Method creating MetricData objects and add them to the metrics array.
        '''
        for metric_type in metric_values.keys():
            metric_val = None
            pvalue_val = None
            if 'pvalue' not in metric_type:
                pval_col = f'{metric_type}_pvalue'
                if pval_col in metric_values.keys():
                    if metric_values[pval_col] not in [None,np.nan,'nan','']:
                        pvalue_val = metric_values[pval_col]
                if metric_values[metric_type] not in [None,np.nan,'nan','']:
                    metric_val = metric_values[metric_type]
                if metric_val != None:
                    metric_data = MetricData(metric_type,metric_val,pvalue_val)
                    self.metrics.append(metric_data)


    def get_cohort_label(self):
        sample = self.data['sample']
        cohorts = [x.name_short for x in sample.cohorts.all()]
        cohort_label = '_'.join(sorted(cohorts))
        if cohort_label in ['MEC','MESA','UKB_Withheld']:
            sample_anc = sample.ancestry_broad
            if sample_anc in self.ancestries.keys():
                cohort_label = f'{cohort_label}_{self.ancestries[sample_anc]}'
        self.data['cohort_label'] = cohort_label



    @transaction.atomic
    def create_model(self):
        '''
        Create an instance of the Performance model.
        Return type: Performance model
        '''
        try:
            with transaction.atomic():
                self.model = Performance(**self.data)
                self.model.save()

            # Create associated Metric objects
            for metric in self.metrics:
                metric_model = metric.create_model(self.model)

        except IntegrityError as e:
            self.model = None
            self.parsing_report_error_import(e)
            print('Error with the creation of the Performance(s) and/or the Metric(s)')

        return self.model
