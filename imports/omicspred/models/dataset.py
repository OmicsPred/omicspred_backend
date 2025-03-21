from django.db import IntegrityError, transaction
import logging
from imports.generic_model import GenericData
from omicspred.models import Dataset, Species
from .publication import PublicationData
from .platform import PlatformData
from .tissue import TissueData


logger = logging.getLogger(__name__)

class DatasetData(GenericData):

    omics_data_types = {
        'Transcriptomics': 'gene expression',
        'Proteomics': 'protein',
        'Metabolomics': 'metabolite'
    }

    def __init__(self,publication:PublicationData,platform:PlatformData,tissue:TissueData,data_type:str,species:str,name:str=None):
        GenericData.__init__(self)
        self.publication = publication
        self.platform = platform
        self.tissue = tissue
        self.scores_count = 1
        self.omics_count = 1
        if name:
            self.name = name
            self.data['name'] = name
        if data_type in self.omics_data_types.keys():
            self.data['omics_type'] = self.omics_data_types[data_type]
        self.data['scores_count'] = 0
        self.data['omics_count'] = 0
        # Species
        try:
            species_model = Species.objects.get(name_latin__iexact=species)
            self.data['species'] = species_model
        except Species.DoesNotExist:
            try:
                species_model = Species.objects.get(name__iexact=species)
                self.data['species'] = species_model
            except Species.DoesNotExist:
                print(f"Can't find the species '{species}' in the database")


    def add_score(self):
        self.data['scores_count'] += 1
        self.data['omics_count'] += 1


    def check_model_exist(self):
        '''
        Check if a Dataset model already exists.
        Return type: Dataset object (omicspred.models) or None
        '''
        try:
            if self.name:
                dataset = Dataset.objects.get(
                    name__iexact=self.data['name'],
                    publication__pmid = self.publication.pmid,
                    platform__name = self.platform.name,
                    platform__version = self.platform.version,
                    tissue__label = self.tissue.label,
                    scores_count = self.data['scores_count']
                )
            else:
                dataset = Dataset.objects.get(
                    publication__pmid = self.publication.pmid,
                    platform__name = self.platform.name,
                    platform__version = self.platform.version,
                    tissue__label = self.tissue.label,
                    scores_count = self.data['scores_count']
                )
            self.model = dataset
            # ! WARNING might need to check the samples as well
        except Dataset.DoesNotExist:
            self.model = None


    @transaction.atomic
    def create_model(self):
        '''
        Create an instance of the Score model.
        Return type: Score model
        '''
        try:
            with transaction.atomic():
                self.check_model_exist()
                if not self.model:
                    self.model = Dataset()
                    self.data['publication'] = self.publication.create_model()
                    self.data['platform'] = self.platform.create_model()
                    self.data['tissue'] = self.tissue.create_model()
                    for field, val in self.data.items():
                        setattr(self.model, field, val)
                    self.model.save()

        except IntegrityError as e:
            self.model = None
            logger.error(f'Error with the creation of the Dataset(s): {e}')
            # print(f'Error with the creation of the Score(s): {e}')
        return self.model