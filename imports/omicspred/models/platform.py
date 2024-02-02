from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from omicspred.models import Platform, PlatformAdditional


class PlatformData(GenericData):

    def __init__(self,name,type,full_name=None,technic=None,version=None):
        GenericData.__init__(self)
        self.data = {
            'name': name,
            'type': type
        }
        if full_name:
            self.data['full_name'] = full_name
        if technic:
            self.data['technic'] = technic
        if version:
            self.data['version'] = version
    

    def check_platform_context(self):
        '''
        Check if a Platform model already exists.
        Return type: Platform model
        '''
        try:
            platform = Platform.objects.get(name=self.data['name'])
            self.model = platform
        except Platform.DoesNotExist:
            self.model = None


    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the Platform model.
        Return type: Platform model
        '''
        try:
            with transaction.atomic():
                self.check_platform_context()
                if not self.model:
                    self.model = Platform()
                    for field, val in self.data.items():
                        setattr(self.model, field, val)
                    self.model.save()
        except IntegrityError as e:
            self.model = None
            print('Error with the creation of the Platform')

        return self.model




class PlatformAdditionalData(GenericData):

    def __init__(self,platform,publication,omics_count,omics_type,tissue_id,cohorts):
        GenericData.__init__(self)
        self.cohorts = cohorts
        self.data = {
            'platform': platform,
            'publication': publication,
            'omics_count': omics_count,
            'omics_type': omics_type,
            'tissue_id': tissue_id
        }


    def check_platform_additional_context(self):
        '''
        Check if a PlatformAdditional model already exists.
        Return type: PlatformAdditional model
        '''
        try:
            platform_additional = PlatformAdditional.objects.get(platform__id=self.data['platform'].id, publication__id=self.data['publication'].id)
            self.model = platform_additional
        except PlatformAdditional.DoesNotExist:
            self.model = None


    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the PlatformAdditional model.
        Return type: PlatformAdditional model
        '''
        try:
            with transaction.atomic():
                self.check_platform_additional_context()
                if not self.model:
                    self.model = PlatformAdditional()
                    for field, val in self.data.items():
                        setattr(self.model, field, val)
                    self.model.save()
                    for cohort in self.cohorts:
                        self.model.cohorts.add(cohort)
                        self.model.save()
        except IntegrityError as e:
            self.model = None
            print('Error with the creation of the PlatformAdditional')

        return self.model