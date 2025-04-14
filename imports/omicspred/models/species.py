from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from omicspred.models import Species


class SpeciesData(GenericData):

    taxonomy_list = {
        'Bos taurus': {
            'name': 'Cow',
            'taxonomy_id': 9913
        },
        'Homo sapiens': {
            'name': 'Human',
            'taxonomy_id': 9606
        },
        'Rattus norvegicus': {
            'name': 'Rat',
            'taxonomy_id': 10116
        }
    }

    def __init__(self,name:str):
        GenericData.__init__(self)
        self.name = name
        if name in self.taxonomy_list.keys():
            self.data = {
                'name_latin': name,
                'name': self.taxonomy_list[name]['name'],
                'taxonomy_id': self.taxonomy_list[name]['taxonomy_id']
            }


    def check_model_exist(self):
        '''
        Check if a Species model already exists.
        '''
        try:
            self.model = Species.objects.get(name_latin=self.name)
            #print(f'Cohort {self.name} found in the DB')
        except Species.DoesNotExist:
            self.model = None


    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the Species model.
        Return type: Species model
        '''
        try:
            with transaction.atomic():
                self.check_model_exist()
                if not self.model:
                    print(f"Species {self.name}: new model")
                    self.model = Species()
                    for field, val in self.data.items():
                        setattr(self.model, field, val)
                    self.model.save()
                else:
                    print(f"Species {self.name}: existing model")
        except IntegrityError as e:
            self.model = None
            print(f'Error with the creation of the Species: {e}')

        return self.model
