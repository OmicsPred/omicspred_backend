import numpy as np
import json
from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from omicspred.models import Gene, Protein, Metabolite, Pathway


class GeneData(GenericData):

    def __init__(self,external_id=None,name=None):
        GenericData.__init__(self)
        self.external_id = external_id
        self.name = name
        self.data_id = ''
        if external_id:
            self.data_id += external_id
        if name:
            self.data_id += name


    def check_model_exist(self):
        '''
        Check if a Gene model already exists.
        '''
        try:
            gene = None
            if self.external_id:
                gene = Gene.objects.get(external_id__iexact=self.external_id)
            elif self.name and self.name not in [None,np.nan,'nan','']:
                gene = Gene.objects.get(name__iexact=self.name)
            # if self.name and self.name not in [None,np.nan,'nan',''] and self.external_id:
            #     gene = Gene.objects.get(name__iexact=self.name, external_id__iexact=self.external_id)
            # elif self.name and self.name not in [None,np.nan,'nan','']:
            #     gene = Gene.objects.get(name__iexact=self.name)
            # elif self.external_id:
            #     gene = Gene.objects.get(external_id__iexact=self.external_id)
            self.model = gene
        except Gene.DoesNotExist:
            self.model = None
            # try:
            #     if self.external_id and self.name and self.name not in [None,np.nan,'nan','']:
            #         gene = Gene.objects.get(name__iexact=self.name)
            #     self.model = gene
            # except Gene.DoesNotExist:
            #     self.model = None


    def update_gene_external_id(self):
        '''
        Update existing Gene model by adding its Ensembl ID
        '''
        self.model.external_id = self.external_id
        self.model.external_id_source = 'Ensembl'
        self.model.save()


    def update_gene_name(self):
        '''
        Update existing Gene model by adding its name
        '''
        self.model.name = self.name
        self.model.save()

    def update_gene_synonym(self):
        '''
        Update existing Gene model by adding its name
        '''
        syn_found = False

        if self.model.synonyms:
            model_synonyms = self.model.synonyms
            for syn in model_synonyms:
                if syn['name'] == self.name:
                    syn_found = True
                    break
            if syn_found == False:
                model_synonyms.append({'name': self.name})
                self.model.synonyms = model_synonyms
                self.model.save()
        else:
            self.model.synonyms = [{'name': self.name}]
            self.model.save()


    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the Gene model.
        Return type: Gene model
        '''
        try:
            with transaction.atomic():
                self.check_model_exist()
                # Create Gene model
                if not self.model:
                    self.model = Gene()
                    if self.name and self.name not in [None,np.nan,'nan','']:
                        self.model.name=self.name
                    if self.external_id:
                        self.model.external_id=self.external_id
                        if self.external_id.startswith('ENSG'):
                            self.model.external_id_source = 'Ensembl'
                    self.model.save()
                # Update Gene model
                else:
                    if not self.model.external_id and self.external_id:
                        self.update_gene_external_id()
                    elif self.name:
                        if not self.model.name:
                            self.update_gene_name()
                        elif self.name != self.model.name:
                            self.update_gene_synonym()
        except IntegrityError as e:
            self.model = None
            print(f'Error with the creation of the Gene: {e}')

        return self.model



class ProteinData(GenericData):

    def __init__(self,external_id=None,name=None,gene=None):
        GenericData.__init__(self)
        self.external_id = external_id
        self.name = name
        self.gene = gene
        self.data_id = ''
        if external_id:
            self.data_id += external_id
        if name:
            self.data_id += name


    def check_model_exist(self):
        '''
        Check if a Protein model already exists.
        '''
        try:
            protein = None
            if self.name and self.name not in [None,np.nan,'nan',''] and self.external_id:
                protein = Protein.objects.get(name__iexact=self.name, external_id__iexact=self.external_id)
            elif self.name and self.name not in [None,np.nan,'nan','']:
                protein = Protein.objects.get(name__iexact=self.name)
            elif self.external_id:
                protein = Protein.objects.get(external_id__iexact=self.external_id)
            self.model = protein
        except Protein.DoesNotExist:
            self.model = None
            try:
                protein = Protein.objects.get(external_id__iexact=self.external_id)
                self.model = protein
            except Protein.DoesNotExist:
                self.model = None


    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the Protein model.
        Return type: Protein model
        '''
        try:
            with transaction.atomic():
                self.check_model_exist()
                if not self.model:
                    self.model = Protein()
                    if self.name and self.name not in [None,np.nan,'nan','']:
                        self.model.name=self.name
                    if self.gene:
                        self.model.gene=self.gene
                    self.model.external_id=self.external_id
                    self.model.external_id_source = 'UniProt'
                    self.model.save()
        except IntegrityError as e:
            self.model = None
            print(f'Error with the creation of the Protein: {e}')

        return self.model


class MetaboliteData(GenericData):

    def __init__(self,external_id=None,name=None,pathway_group=None,pathway_subgroup=None):
        GenericData.__init__(self)
        self.external_id = external_id
        self.name = name
        self.data_id = ''
        if external_id:
            self.data_id += external_id
        if name:
            self.data_id += name
        if self.name not in [None,np.nan,'nan','']:
            self.data['name'] = self.name
        if self.external_id not in [None,np.nan,'nan','']:
            self.data['external_id'] = self.external_id
            self.data['external_id_source'] = 'Metabolon'
        if pathway_group not in [None,np.nan,'nan','']:
            self.data['pathway_group'] = pathway_group
        if pathway_subgroup not in [None,np.nan,'nan','']:
            self.data['pathway_subgroup'] = pathway_subgroup


    def check_model_exist(self):
        '''
        Check if a Metabolite model already exists.
        Return type: Metabolite model
        '''
        try:
            metabolite = None
            if self.name not in [None,np.nan,'nan',''] and self.external_id:
                metabolite = Metabolite.objects.get(name__iexact=self.name, external_id__iexact=self.external_id)
            elif self.name not in [None,np.nan,'nan','']:
                metabolite = Metabolite.objects.get(name__iexact=self.name)
            elif self.external_id:
                metabolite = Metabolite.objects.get(external_id__iexact=self.external_id)
            self.model = metabolite
        except Metabolite.DoesNotExist:
            self.model = None
            try:
                if self.name not in [None,np.nan,'nan','']:
                    metabolite = Metabolite.objects.get(name__iexact=self.name)
                else:
                    metabolite = Metabolite.objects.get(external_id__iexact=self.external_id)
                self.model = metabolite
            except Metabolite.DoesNotExist:
                self.model = None


    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the Metabolite model.
        Return type: Metabolite model
        '''
        try:
            with transaction.atomic():
                self.check_model_exist()
                if not self.model:
                    self.model =  Metabolite()
                    for field, val in self.data.items():
                        setattr(self.model, field, val)
                    self.model.save()
        except IntegrityError as e:
            self.model = None
            print(f'Error with the creation of the Metabolite: {e}')
        return self.model



class PathwayData(GenericData):

    def __init__(self,external_id=None,name=None):
        self.external_id = external_id
        self.name = name


    def check_model_exist(self):
        '''
        Check if a Pathway model already exists.
        '''
        try:
            pathway = None
            if self.name not in [None,np.nan,'nan',''] and self.external_id:
                pathway = Pathway.objects.get(name__iexact=self.name, external_id__iexact=self.external_id)
            elif self.name not in [None,np.nan,'nan','']:
                pathway = Pathway.objects.get(name__iexact=self.name)
            elif self.external_id:
                pathway = Pathway.objects.get(external_id__iexact=self.external_id)
            self.model = pathway
        except Pathway.DoesNotExist:
            self.model = None
            try:
                if self.name not in [None,np.nan,'nan','']:
                    pathway = Pathway.objects.get(name__iexact=self.name)
                else:
                    pathway = Pathway.objects.get(external_id__iexact=self.external_id)
                self.model = pathway
            except Pathway.DoesNotExist:
                self.model = None


    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the Pathway model.
        Return type: Pathway model
        '''
        try:
            with transaction.atomic():
                self.check_model_exist()
                if not self.model:
                    if self.name not in [None,np.nan,'nan',''] or self.external_id:
                        self.model = Pathway()
                        if self.name not in [None,np.nan,'nan','']:
                            self.model.name=self.name
                        if self.external_id:
                            self.model.external_id=self.external_id
                        self.model.save()
        except IntegrityError as e:
            self.model = None
            print(f'Error with the creation of the Pathway: {e}')

        return self.model
