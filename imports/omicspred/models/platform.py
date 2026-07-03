from django.db import IntegrityError, transaction
import logging
from imports.generic_model import GenericData
from omicspred.models import Platform, PlatformMaster, Dataset


logger = logging.getLogger(__name__)

class PlatformMasterData(GenericData):

    def __init__(self,name,type,full_name=None,technique=None):
        GenericData.__init__(self)
        self.name = name
        self.data = {
            'name': name,
            'type': type
        }
        if full_name:
            self.data['full_name'] = full_name
        if technique:
            self.data['technique'] = technique


    def check_model_exist(self):
        '''
        Check if a PlatformMaster model already exists.
        Return type: PlatformMaster model
        '''
        try:
            platform = PlatformMaster.objects.get(name__iexact=self.data['name'],type__iexact=self.data['type'])
            self.model = platform
        except PlatformMaster.DoesNotExist:
            self.model = None


    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the Platform model.
        Return type: Platform model
        '''
        try:
            with transaction.atomic():
                self.check_model_exist()
                if not self.model:
                    self.model = PlatformMaster()
                    for field, val in self.data.items():
                        setattr(self.model, field, val)
                    self.model.save()
        except IntegrityError as e:
            self.model = None
            logger.error(f'Error with the creation of the PlatformMaster: {e}')
            # print('Error with the creation of the PlatformMaster')
        return self.model


class PlatformData(GenericData):

    def __init__(self,platform_master,version=None):
        GenericData.__init__(self)
        self.name = platform_master.name
        self.platform_master_data = platform_master
        self.version = version
        self.data = {
            'name': platform_master.name
        }
        if version:
            self.data['version'] = version


    def check_model_exist(self):
        '''
        Check if a Platform model already exists.
        Return type: Platform model
        '''
        try:
            if 'version' in self.data.keys():
                platform = Platform.objects.get(name__iexact=self.data['name'], version__iexact=self.data['version'])
            else:
                platform = Platform.objects.get(name__iexact=self.data['name'])
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
                self.check_model_exist()
                if not self.model:
                    # PlatformMaster
                    platform_master = self.platform_master_data.check_model_exist()
                    if not platform_master:
                        platform_master = self.platform_master_data.create_model()
                    self.data['platform_master'] = platform_master
                    # Platform
                    self.model = Platform()
                    for field, val in self.data.items():
                        setattr(self.model, field, val)
                    self.model.save()
        except IntegrityError as e:
            self.model = None
            print(f'Error with the creation of the Platform: {e}')

        return self.model