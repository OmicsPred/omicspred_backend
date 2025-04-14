from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from omicspred.models import Metric

class MetricData(GenericData):

    # Type of metric
    type_choices = {
        'R2' : "Pearson's correlation",
        # 'R2_pvalue'  : "Pearson's correlation",
        'Rho': "Spearman's rank correlation",
        # 'Rho_pvalue' : "Spearman's rank correlation",
        # 'MissingRate': "Variant Missing Rate",
        'MatchingRate': "Variant Match Rate"
    }

    # Metric method
    name_common = {
        'OR': ('Odds Ratio', 'OR'),
        'HR': ('Hazard Ratio', 'HR'),
        'AUROC': ('Area Under the Receiver-Operating Characteristic Curve', 'AUROC'),
        'Cindex': ('Concordance Statistic', 'C-index'),
        'R2': ('Proportion of the variance explained', 'R2'),
        # 'R2_pvalue': ('p-value', 'p-value'),
        'Rho': ('Spearman correlation coefficient', 'Rho'),
        # 'Rho_pvalue': ('p-value', 'p-value'),
        # 'MissingRate': ('Missing Rate', 'Missing Rate')
        'MatchingRate': ('Variant Match Rate', 'Match Rate')
    }

    def __init__(self,metric_data):
        GenericData.__init__(self)
        estimate = metric_data['estimate']
        if 'E' in str(estimate):
            estimate = estimate.replace('E','e')
            estimate = float(estimate)
        self.name = metric_data['name'].strip()
        self.data = {
            'type': self.type_choices[self.name],
            'estimate': estimate
        }
        if 'pvalue' in metric_data.keys():
            self.data['pvalue'] = metric_data['pvalue']

        # Add extra information
        if self.name in self.name_common.keys():
            self.add_data('name', self.name_common[self.name][0])
            self.add_data('name_short', self.name_common[self.name][1])
        else:
            self.name, self.value = self.value.split('=')
            self.name = self.name.strip()
            self.add_data('name', self.name)

        if not 'name_short' in self.data and len(self.name) <= 20:
            self.add_data('name_short', self.name)


    # def set_names(self):
    #     ''' Set the metric names (short and long). '''
    #     if self.name in self.name_common.keys():
    #         self.add_data('name', self.name_common[self.name][0])
    #         self.add_data('name_short', self.name_common[self.name][1])
    #     else:
    #         self.name, self.value = self.value.split('=')
    #         self.name = self.name.strip()
    #         self.add_data('name', self.name)

    #     if not 'name_short' in self.data and len(self.name) <= 20:
    #         self.add_data('name_short', self.name)


    @transaction.atomic
    def create_model(self,performance):
        '''
        Create an instance of the Metric model.
        Return type: Metric model
        '''
        # self.set_names()
        try:
            with transaction.atomic():
                self.model = Metric(**self.data)
                self.model.performance = performance
                self.model.save()
        except IntegrityError as e:
            print(f'Error with the creation of the Metric: {e}')
        return self.model
