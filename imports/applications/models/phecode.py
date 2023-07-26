from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from applications.models import Phecode

class PhecodeData(GenericData):

    def __init__(self,data):
        GenericData.__init__(self)

        # 'id': data_info['PheCode'],
        #     'name': data_info['Phenotype'],
        #     'category': data_info['Category']
        self.id = data['id']
        self.data = data

    def check_phecode(self):
        '''
        Check if a Phecode model already exists.
        Return type: Phecode model
        '''
        try:
            phecode = Phecode.objects.using(self.applications_db).get(id=self.id)
            self.model = phecode
        except Phecode.DoesNotExist:
            self.model = None
        

    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the Phecode model.
        Return type: Cohort model
        '''
        try:
            with transaction.atomic():
                self.check_phecode()
                if not self.model:
                    self.model = Phecode()
                    for field, val in self.data.items():
                        setattr(self.model, field, val)
                    self.model.save(using=self.applications_db)
        except IntegrityError as e:
            self.model = None
            print('Error with the creation of the Phecode')

        return self.model
