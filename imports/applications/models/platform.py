from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from applications.models import PlatformApplications
from omicspred.models import Platform as OPPlatform


class PlatformData(GenericData):

    def __init__(self,data):
        GenericData.__init__(self)
        self.name = data['name']
        self.data = data


    def check_platform(self):
        '''
        Check if a Platform, model already exists in the Applications DB.
        Return type: Platform model (Applications)
        '''
        try:
            platform = PlatformApplications.objects.using(self.applications_db).get(name__iexact=self.name)
            self.model = platform
        except PlatformApplications.DoesNotExist:
            self.model = None


    def get_omicspred_platform(self):
        '''
        Get Platform model from Omicspred DB
        Return type: Platform model (Omicspred)
        '''
        try:
            platform = OPPlatform.objects.get(name__iexact=self.name)
            return platform
        except OPPlatform.DoesNotExist:
            return None


    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the PlatformApplications model.
        Return type: PlatformApplications model
        '''
        try:
            with transaction.atomic():
                self.check_platform()
                if not self.model:
                    self.model = PlatformApplications()
                    op_platform_model = self.get_omicspred_platform()
                    if op_platform_model:
                        self.model.name=op_platform_model.name
                        self.model.full_name=op_platform_model.full_name
                        self.model.version=op_platform_model.version
                        self.model.technic=op_platform_model.technic
                        self.model.type=op_platform_model.type
                    else:
                        for field, val in self.data.items():
                            setattr(self.model, field, val)
                    self.model.save(using=self.applications_db)

        except IntegrityError as e:
            self.model = None
            print('Error with the creation of the PlatformApplications')

        return self.model
