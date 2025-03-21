from django.db import IntegrityError, transaction
import logging
from imports.generic_model import GenericData
from omicspred.models import Score, Dataset


logger = logging.getLogger(__name__)

class ScoreData(GenericData):

    def __init__(self,score_data:dict):
        GenericData.__init__(self)
        self.dataset_tag = None
        for item in score_data.keys():
            if score_data[item]:
                 self.data[item] = score_data[item]


    def set_dataset_tag(self,dataset_tag:str):
        self.dataset_tag = dataset_tag


    def get_dataset_tag(self):
        return self.dataset_tag


    def add_dataset_model(self,dataset:Dataset):
        self.data['dataset'] = dataset
        self.data['species'] = dataset.species


    @transaction.atomic
    def create_model(self):
        '''
        Create an instance of the Score model.
        Return type: Score model
        '''
        try:
            with transaction.atomic():
                self.model = Score()
                self.model.set_score_ids(self.next_id_number(Score, 'num'))
                for field, val in self.data.items():
                    setattr(self.model, field, val)
                self.model.save()

                if 'genes' in self.additional_data.keys():
                    for gene in self.additional_data['genes']:
                        gene_model = gene.create_model()
                        self.model.genes.add(gene_model)
                if 'proteins' in self.additional_data.keys():
                    for protein in self.additional_data['proteins']:
                        protein_model = protein.create_model()
                        self.model.proteins.add(protein_model)
                if 'metabolites' in self.additional_data.keys():
                    for metabolite in self.additional_data['metabolites']:
                        metabolite_model = protein.create_model()
                        self.model.metabolites.add(metabolite_model)

        except IntegrityError as e:
            self.model = None
            logger.error(f'Error with the creation of the Score(s): {e}')
        return self.model
