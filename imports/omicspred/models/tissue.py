import logging
import re
import requests
from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from omicspred.models import Tissue


logger = logging.getLogger(__name__)

class TissueData(GenericData):

    def __init__(self,id:str):
        GenericData.__init__(self)
        self.id = id
        self.data['type'] = 'tissue'

    def fetch_tissue_information(self):
        # tissue_id = self.id.replace('_',':')
        tissue_id = self.id.strip()
        ontology = 'efo'
        if not tissue_id.startswith('EFO'):
            ontology_components = re.split(r'(_|:)', tissue_id)
            ontology = ontology_components[0]
            ontology = ontology.lower()
            print(f"    > {tissue_id} ({ontology})")
        response = requests.get(f"https://www.ebi.ac.uk/ols4/api/ontologies/{ontology}/terms?obo_id={tissue_id}")#, headers={"Content-Type":"json"})
        response = response.json()['_embedded']['terms']
        if len(response) == 1:
            response = response[0]
            self.label = response['label']
            self.data['id'] = self.id
            self.data['label'] = self.label
            self.data['url'] = response['iri']

            # Make description
            try:
                desc = response['obo_definition_citation'][0]
                str_desc = desc['definition']
                for x in desc['oboXrefs']:
                    if x['database'] != None:
                        if x['id'] != None:
                            str_desc += ' [{}: {}]'.format(x['database'], x['id'])
                        else:
                            str_desc += ' [{}]'.format(x['database'])
                self.data['description'] = str_desc
            except:
                self.data['description'] = response['description']
            if self.data['description'] == '[]':
                self.data['description'] = None


    def check_model_exist(self):
        '''
        Check if an Tissue model already exists.
        '''
        try:
            tissue = Tissue.objects.get(id=self.id)
            self.model = tissue
        except Tissue.DoesNotExist:
            self.model = None


    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the Tissue model.
        Return type: Tissue model
        '''
        try:
            with transaction.atomic():
                self.check_model_exist()
                if not self.model:
                    self.model = Tissue()
                    for field, val in self.data.items():
                        setattr(self.model, field, val)
                    self.model.save()
        except IntegrityError as e:
            self.model = None
            logger.error(f'Error with the creation of the Tissue: {e}')

        return self.model
