from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from omicspred.models import Metric

class MetricData(GenericData):

    # Type of metric
    type_choices = {
        'R2' : "Pearson's correlation",
        'R2_pvalue'  : "Pearson's correlation",
        'Rho': "Spearman's rank correlation",
        'Rho_pvalue' : "Spearman's rank correlation",
        'MissingRate': "Variant Missing Rate"
    }

    # Metric method
    name_common = {
        'OR': ('Odds Ratio', 'OR'),
        'HR': ('Hazard Ratio', 'HR'),
        'AUROC': ('Area Under the Receiver-Operating Characteristic Curve', 'AUROC'),
        'Cindex': ('Concordance Statistic', 'C-index'),
        'R2': ('Proportion of the variance explained', 'R2'),
        'R2_pvalue': ('p-value', 'p-value'),
        'Rho': ('Spearman correlation coefficient', 'Rho'),
        'Rho_pvalue': ('p-value', 'p-value'),
        'MissingRate': ('Missing Rate', 'Missing Rate')
    }

    def __init__(self,name,value,pvalue=None):
        GenericData.__init__(self)
        if 'E' in str(value):
            value = value.replace('E','e')
            value = float(value)
        self.name = name.strip()
        self.data = {
            'performance_type': self.type_choices[self.name],
            'estimate': value
        }
        if pvalue:
            self.data['pvalue'] = pvalue


    def set_names(self):
        ''' Set the metric names (short and long). '''
        if self.name in self.name_common:
            self.add_data('name', self.name_common[self.name][0])
            self.add_data('name_short', self.name_common[self.name][1])
        else:
            self.name, self.value = self.value.split('=')
            self.name = self.name.strip()
            self.add_data('name', self.name)

        if not 'name_short' in self.data and len(self.name) <= 20:
            self.add_data('name_short', self.name)


    @transaction.atomic
    def create_model(self,performance):
        '''
        Create an instance of the Metric model.
        Return type: Metric model
        '''
        self.set_names()
        try:
            with transaction.atomic():
                self.model = Metric(**self.data)
                self.model.performance = performance
                self.model.save()
        except IntegrityError as e:
            print('Error with the creation of the Metric')
        return self.model
