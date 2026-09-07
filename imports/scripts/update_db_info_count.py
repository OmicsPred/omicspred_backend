from omicspred.models import *

def run():
    current_info = {}
    for info in Info.objects.all():
        info_name = info.name
        current_info[info_name] = info

    # Datasets
    new_info = {
        'datasets': Dataset.objects.count(),
        'scores': Score.objects.count(),
        'publications': Publication.objects.count(),
        'platforms': PlatformMaster.objects.count(),
        'pathways': Pathway.objects.count(),
        'phenotypes': Phenotype.objects.count(),
        'phewas': ScorePheWAS.objects.count(),
        'tissues': Tissue.objects.filter(type='tissue').count()
    }

    for info_name in new_info.keys():
        if info_name in current_info.keys():
            current_info_model = current_info[info_name]
            current_info_model.value = new_info[info_name]
            current_info_model.save()
            print(f"- Update '{info_name}' count ({new_info[info_name]})")
        else:
            info_model = Info(
                name = info_name,
                value = new_info[info_name]
            )
            info_model.save()
            print(f"- Create '{info_name}' count ({new_info[info_name]})")