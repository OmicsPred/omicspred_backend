from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from applications.models import SampleApplications


class SampleData(GenericData):

    def __init__(self,data):
        GenericData.__init__(self)
        self.data = data

    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the SampleApplications model.
        Return type: SampleApplications model
        '''
        try:
            with transaction.atomic():
                self.model = SampleApplications()
                for field, val in self.data.items():
                    setattr(self.model, field, val)
                self.model.save(using=self.applications_db)
        except IntegrityError as e:
            self.model = None
            print('Error with the creation of the SampleApplications')

        return self.model