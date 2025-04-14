from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from omicspred.models import Cohort


class CohortData(GenericData):

    def __init__(self,name_short:str,cohort_data:dict):
        GenericData.__init__(self)
        self.name_short = name_short
        for item in cohort_data.keys():
            if cohort_data[item]:
                 self.data[item] = cohort_data[item]
        # self.cohort_tuple = (self.name,self.name_full,self.url)

    def get_data(self,attribute:str):
        if attribute in self.data.keys():
            return self.data[attribute]

    def check_model_exist(self):
        '''
        Check if a Cohort model already exists.
        '''
        name = self.get_data('name_short')
        name_full = self.get_data('name_full')
        try:
            cohort = None
            if name_full:
                cohort = Cohort.objects.get(name_short__iexact=name, name_full__iexact=name_full)
            else:
                cohort = Cohort.objects.get(name_short__iexact=name)
            if cohort:
                self.model = cohort
            #print(f'Cohort {self.name} found in the DB')
        except Cohort.DoesNotExist:
            self.model = None
            try:
                if name_full:
                    cohort = Cohort.objects.get(name_short__iexact=name)
                    # Short name = long name
                    if name == name_full:
                        self.model = cohort
                    else:
                        print(f'A existing cohort has been found in the DB with the ID "{name}" ({name_full}). However the long name differs.')
            except Cohort.DoesNotExist:
                print(f'New cohort "{name}" / "{name_full}".')
                self.model = None
            except:
                print(f'ERROR with cohort {name} duplicated!')
        except:
            print(f'ERROR with cohort {name} ({name_full}) duplicated!')


    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the Cohort model.
        Return type: Cohort model
        '''
        try:
            with transaction.atomic():
                self.check_model_exist()
                if not self.model:
                    print(f"Cohort {self.name_short}: new model")
                    self.model = Cohort()
                    if 'name_short' in self.data.keys():
                        self.model.name_short=self.data['name_short']
                    if 'name_full' in self.data.keys():
                        self.model.name_full=self.data['name_full']
                    if 'url' in self.data.keys():
                        self.model.url=self.data['url']
                    self.model.save()
                else:
                    print(f"Cohort {self.name_short}: existing model")
        except IntegrityError as e:
            self.model = None
            print(f'Error with the creation of the Cohort: {e}')

        return self.model
