from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from applications.models import ScoreApplications
from omicspred.models import Score


class ScoreData(GenericData):

    def __init__(self,data):
        GenericData.__init__(self)
        self.id = data['score_id']
        self.data = data


    def check_score(self):
        '''
        Check if a ScoreApplications model already exists.
        Return type: ScoreApplications model
        '''
        try:
            score_app = ScoreApplications.objects.using(self.applications_db).get(score_id=self.id)
            self.model = score_app
        except ScoreApplications.DoesNotExist:
            self.model = None

    def check_omicspred_id(self):
        '''
        Check if a Score model (Omicspred) exists with the given ID.
        Return type: Score model
        '''
        try:
            score = Score.objects.get(id=self.id)
            return True
        except Score.DoesNotExist:
            return False


    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the ScoreApplications model.
        Return type: ScoreApplications model
        '''
        try:
            with transaction.atomic():
                self.check_score()
                if not self.model:
                    op_id_exist = self.check_omicspred_id()
                    if op_id_exist:
                        self.model = ScoreApplications()
                        for field, val in self.data.items():
                            setattr(self.model, field, val)
                        self.model.save(using=self.applications_db)
        except IntegrityError as e:
            self.model = None
            print('Error with the creation of the ScoreApplications')

        return self.model
