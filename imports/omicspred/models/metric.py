from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from omicspred.models import Metric

class MetricData(GenericData):

    # Type of metric
    type_choices = {
        'R2' : "Pearson's correlation",
        'Rho': "Spearman's rank correlation",
        'MatchingRate': "Variant Match Rate"
    }

    # Metric method
    name_common = {
        'OR': ('Odds Ratio', 'OR'),
        'HR': ('Hazard Ratio', 'HR'),
        'AUROC': ('Area Under the Receiver-Operating Characteristic Curve', 'AUROC'),
        'Cindex': ('Concordance Statistic', 'C-index'),
        'R2': ('Proportion of the variance explained', 'R2'),
        'Rho': ('Spearman correlation coefficient', 'Rho'),
        'MatchingRate': ('Variant Match Rate', 'Match Rate')
    }


    def __init__(self,metric_data):
        GenericData.__init__(self)
        estimate = self.convert_values(metric_data['estimate'])
        self.name = metric_data['name'].strip()
        self.data = {
            'type': self.type_choices[self.name],
            'estimate': estimate
        }
        if 'pvalue' in metric_data.keys():
            self.data['pvalue'] = self.convert_values(metric_data['pvalue'])

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


    def convert_values(self,value):
        if 'E' in str(value):
            value = value.replace('E','e')
        # Limit to 5 decimals, e.g. 0.111222333 -> 0.11122
        if len(str(float(value))) > 7: # first digit + dot + at least 6 decimals
            if 'e' in str(value):
                value = "{:.5e}".format(value)
            elif value < 0.001:
                value = "{:.5e}".format(value)
            else:
                value = "{:.5f}".format(value)
                value = float(value)
        return value

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
