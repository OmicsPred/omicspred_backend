from omicspred.models import Score, Dataset


def datasets_update():
    ''' Update the dataset models '''
    datasets = Dataset.objects.all().order_by('num')

    for dataset in datasets:
        if dataset.method_name in ['', None]:
            # Update the 'method_name'
            methods = dataset.dataset_score.values_list('method_name').distinct('method_name')
            
            if methods:
                methods = list(methods)
                method_names = methods[0]
                print(f"> Dataset {dataset.id}: {method_names}")
                if len(method_names) > 0:
                    dataset.method_name = ','.join(method_names)
                    dataset.save()


def run():
    datasets_update()