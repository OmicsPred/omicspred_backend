from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from omicspred.models import Score


class ScoreData(GenericData):

    def __init__(self,score_data):
        GenericData.__init__(self)
        num = score_data['id'].replace('OPGS','').lstrip('0')
        self.data['num'] = int(num)
        for item in score_data.keys():
            if score_data[item]:
                 self.data[item] = score_data[item]


    @transaction.atomic
    def create_model(self):
        '''
        Create an instance of the Score model.
        Return type: Score model
        '''
        try:
            with transaction.atomic():
                self.model = Score()
                for field, val in self.data.items():
                    setattr(self.model, field, val)
                self.model.save()

        except IntegrityError as e:
            self.model = None
            print(f'Error with the creation of the Score(s): {e}')
        return self.model
