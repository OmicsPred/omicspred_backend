from django.db.models import Q
from omicspred.models import Dataset
from exports.config import dataset_selection

class DatasetsSelection():

    def __init__(self):
        print(f'dataset_selection: {dataset_selection}')
        ds_keys = list(dataset_selection.keys())
        print(f'dataset_selection keys: {ds_keys}')
        self.dataset_col = ds_keys[0]
        self.dataset_value = dataset_selection[self.dataset_col]
    
    def get_datasets(self) -> list:
        param = self.dataset_col
        param = Q(**{f'{self.dataset_col}':self.dataset_value})

        datasets = Dataset.objects.filter(param).order_by('num')
        return datasets