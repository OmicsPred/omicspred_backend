from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from applications.models import CohortApplications
from omicspred.models import Cohort as OPCohort


class CohortData(GenericData):

    def __init__(self,data):
        GenericData.__init__(self)
        self.name = data['name_short']
        self.data = data

    def check_cohort(self):
        '''
        Check if a CohortApplications model already exists in the Applications DB.
        Return type: CohortApplications model (Applications)
        '''
        try:
            cohort = CohortApplications.objects.using(self.applications_db).get(name_short__iexact=self.name)
            self.model = cohort
        except CohortApplications.DoesNotExist:
            self.model = None


    def get_omicspred_cohort(self):
        '''
        Get Cohort model from Omicspred DB
        Return type: Cohort model (Omicspred)
        '''
        try:
            cohort = OPCohort.objects.get(name_short__iexact=self.name)
            return cohort
        except OPCohort.DoesNotExist:
            return None


    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the CohortApplications model.
        Return type: CohortApplications model
        '''
        try:
            with transaction.atomic():
                self.check_cohort()
                if not self.model:
                    self.model = CohortApplications()
                    op_cohort_model = self.get_omicspred_cohort()
                    if op_cohort_model:
                        self.model.name_short=op_cohort_model.name_short
                        self.model.name_full=op_cohort_model.name_full
                        self.model.url=op_cohort_model.url
                    else:
                        for field, val in self.data.items():
                            setattr(self.model, field, val)
                    self.model.save(using=self.applications_db)

        except IntegrityError as e:
            self.model = None
            print('Error with the creation of the CohortApplications')

        return self.model
