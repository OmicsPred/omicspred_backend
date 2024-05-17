from django.db.models import Q
from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from applications.models import ScoreApplications, MolecularTraitApplications
from omicspred.models import Score


class ScoreData(GenericData):

    def __init__(self,data):
        GenericData.__init__(self)
        self.id = data['score_id']
        self.data = data


    # def check_score(self):
    #     '''
    #     Check if a ScoreApplications model already exists.
    #     Return type: ScoreApplications model
    #     '''
    #     try:
    #         score_app = ScoreApplications.objects.using(self.applications_db).get(score_id=self.id)
    #         self.model = score_app
    #     except ScoreApplications.DoesNotExist:
    #         self.model = None

    def check_omicspred_id(self):
        '''
        Check if a Score model (Omicspred) exists with the given ID.
        Return type: Score model
        '''
        try:
            score = Score.objects.get(id=self.id)
            return score
        except Score.DoesNotExist:
            return None

    def add_molecular_traits(self,mt_type,molecular_traits,mt_list):
        if molecular_traits:
            for molecular_trait in molecular_traits.all():
                mt_pr = MolecularTraitApplications.objects.using(self.applications_db).filter(Q(external_id=molecular_trait.external_id) | Q(name=molecular_trait.name))
                if mt_pr:
                    mt_pr = mt_pr[0]
                else:
                    mt_pr = MolecularTraitApplications(type=mt_type)
                    if molecular_trait.name:
                        mt_pr.name=molecular_trait.name
                    if molecular_trait.external_id:
                        mt_pr.external_id=molecular_trait.external_id
                    mt_pr.save(using=self.applications_db)
                if mt_pr:
                    mt_list.append(mt_pr)
        return mt_list

    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the ScoreApplications model.
        Return type: ScoreApplications model
        '''
        try:
            with transaction.atomic():
                # self.check_score()
                # if not self.model:
                op_obj = self.check_omicspred_id()
                if op_obj:
                    self.model = ScoreApplications()
                    for field, val in self.data.items():
                        setattr(self.model, field, val)
                    self.model.save(using=self.applications_db)
                    ## Molecular traits
                    mt_list = []
                    # Genes
                    genes = op_obj.genes
                    mt_list = self.add_molecular_traits('gene',genes,mt_list)
                    # Protein
                    proteins = op_obj.proteins
                    mt_list = self.add_molecular_traits('protein',proteins,mt_list)
                    # Metabolite
                    metabolites = op_obj.metabolites
                    mt_list = self.add_molecular_traits('metabolite',metabolites,mt_list)

                    if mt_list:
                        for mt in mt_list:
                            self.model.molecular_traits.add(mt)
                        self.model.save(using=self.applications_db)
                else:
                    print(f"- Error: Score {self.id} can't be found in OmicsPred")
        except IntegrityError as e:
            self.model = None
            print('Error with the creation of the ScoreApplications')

        return self.model
