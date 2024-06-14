from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from omicspred.models import Platform, PlatformMaster, Dataset


class PlatformMasterData(GenericData):

    def __init__(self,name,type,full_name=None,technic=None):
        GenericData.__init__(self)
        self.data = {
            'name': name,
            'type': type
        }
        if full_name:
            self.data['full_name'] = full_name
        if technic:
            self.data['technic'] = technic


    def check_platform_context(self):
        '''
        Check if a PlatformMaster model already exists.
        Return type: PlatformMaster model
        '''
        try:
            platform = PlatformMaster.objects.get(name__iexact=self.data['name'],type__iexact=self.data['type'])
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
                    self.model = PlatformMaster()
                    for field, val in self.data.items():
                        setattr(self.model, field, val)
                    self.model.save()
        except IntegrityError as e:
            self.model = None
            print('Error with the creation of the PlatformMaster')

        return self.model


class PlatformData(GenericData):

    def __init__(self,platform_master,version=None):
        GenericData.__init__(self)
        self.data = {
            'name': platform_master.name,
            'platform_master': platform_master
        }
        if version:
            self.data['version'] = version
    

    def check_platform_context(self):
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


class DatasetData(GenericData):

    def __init__(self,platform,publication,omics_count,omics_type,tissue,files_ids,species=None,dataset_name=None):
        GenericData.__init__(self)
        self.data = {
            'platform': platform,
            'publication': publication,
            'omics_count': omics_count,
            'omics_type': omics_type,
            'scores_count': omics_count,
            'files_ids': files_ids,
            'tissue': tissue
        }
        if species:
           self.data['species'] = species
        if dataset_name:
           self.data['name'] = dataset_name



    def check_dataset_context(self):
        '''
        Check if a Dataset model already exists.
        Return type: Dataset model
        '''
        try:
            if 'name' in self.data.keys():
                dataset = Dataset.objects.get(platform__id=self.data['platform'].id, publication__id=self.data['publication'].id, omics_count=self.data['omics_count'], name=self.data['name'])
            else:
                dataset = Dataset.objects.get(platform__id=self.data['platform'].id, publication__id=self.data['publication'].id, omics_count=self.data['omics_count'])
            self.model = dataset
        except Dataset.DoesNotExist:
            self.model = None


    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the Dataset model.
        Return type: Dataset model
        '''
        try:
            with transaction.atomic():
                self.check_dataset_context()
                if not self.model:
                    self.model = Dataset()
                    for field, val in self.data.items():
                        setattr(self.model, field, val)
                    self.model.save()
        except IntegrityError as e:
            self.model = None
            print(f'Error with the creation of the Dataset: {e}')

        return self.model