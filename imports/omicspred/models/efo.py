from django.db import IntegrityError, transaction
from imports.omicspred.models.generic import GenericData
from omicspred.models import EFO


class EFOData(GenericData):

    def __init__(self,data):
        GenericData.__init__(self)
        self.data = data


    def check_efo_context(self):
        '''
        Check if a EFO model already exists.
        Return type: EFO model
        '''
        try:
            efo = EFO.objects.get(id=self.data['id'])
            self.model = efo
            #print(f'Cohort {self.name} found in the DB')
        except EFO.DoesNotExist:
            self.model = None


    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the EFO model.
        Return type: EFO model
        '''
        try:
            with transaction.atomic():
                self.check_efo_context()
                if not self.model:
                    self.model = EFO()
                    for field, val in self.data.items():
                        setattr(self.model, field, val)
                    self.model.save()
        except IntegrityError as e:
            self.model = None
            print('Error with the creation of the EFO')

        return self.model
