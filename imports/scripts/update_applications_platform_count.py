from applications.models import SampleApplications, ScoreApplications

applications_db = 'applications'

def run():
    scores_app = ScoreApplications.objects.using(applications_db).select_related('phecode','platform','cohort').all()

    phecode_platform = {}
    for score_app in scores_app:
        phecode_id = score_app.phecode.id
        platform_name = score_app.platform.name

        if phecode_id not in phecode_platform.keys():
            phecode_platform[phecode_id] = {}
        if platform_name not in phecode_platform[phecode_id].keys():
            phecode_platform[phecode_id][platform_name] = 0
        phecode_platform[phecode_id][platform_name] += 1

    for phecode_id in phecode_platform.keys():
        try:
            sample_app = SampleApplications.objects.using(applications_db).select_related('phecode').get(phecode__id=phecode_id)
            print(f'- {phecode_id}: {phecode_platform[phecode_id]}')
            sample_app.platform_counts = phecode_platform[phecode_id]
            sample_app.save()
        except SampleApplications.DoesNotExist:
            print(f'X {phecode_id}: no entry in SampleApplications')