from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.postgres.fields import DecimalRangeField


class CohortApplications(models.Model):
    """ Class to describe cohorts used in samples """
    name_short = models.CharField('Cohort Short Name', max_length=100, db_index=True)
    name_full = models.CharField('Cohort Full Name', max_length=1000)
    name_others = models.TextField('Previous/other/additional names (e.g. sub-cohorts)', null=True)
    url = models.CharField('Cohort URL', max_length=100)

    def __str__(self):
        return self.name_short


class Phecode(models.Model):
    """ Class for individual Phecode entry """
    # PheWAS identifiers
    id = models.CharField('PheWAS ID', max_length=30, primary_key=True)
    name = models.CharField('PheWAS Name', max_length=150, null=True)
    category = models.CharField('PheWAS Category', max_length=100, null=True)
    
    child_phecode = models.ManyToManyField('self', verbose_name='Children Phecode', symmetrical=False, related_name='parent_phecode')

    @property
    def score_number(self):
        scores = ScoreApplications.objects.select_related('platform').filter(phecode=self)
        data = {}
        for score in scores.all():
            platform = score.platform.name
            if platform in data.keys():
                data[platform] += 1
            else:
                data[platform] = 1
        return data


class PlatformApplications(models.Model):
    """ Class to describe the platform used to get the omics data """
    name = models.CharField('Platform name', max_length=100)
    full_name = models.CharField('Platform full name', max_length=100)
    version = models.CharField('Platform version', max_length=50)
    technic = models.CharField('Platform technic', max_length=100)
    type = models.CharField('Platform type', max_length=100)


class SampleApplications(models.Model):
    sample_number = models.IntegerField('Number of Individuals', null=True)
    sample_cases = models.IntegerField('Number of Cases', null=True)
    sample_percent_female = models.FloatField('Percent of Participants Who are Female', validators=[MinValueValidator(0), MaxValueValidator(100)], null=True)
    sample_age = models.FloatField('Sample Age', null=True)
    sample_age_sd = models.FloatField('Mean standard deviation of Age', null=True)
    phecode = models.ForeignKey(Phecode, on_delete=models.PROTECT, related_name='phecode_sample', verbose_name='Phecode')
    platform_counts = models.JSONField('Associations by platform', null=True)


class ScoreApplications(models.Model):
    """ Class for score association for the application """
    score_id = models.CharField('Omicspred ID', max_length=30, db_index=True)
    omics_name = models.CharField('Omics Entity ID/Name', max_length=150, null=True)
    phecode = models.ForeignKey(Phecode, on_delete=models.PROTECT, related_name='phecode_score', verbose_name='Phecode')
    platform = models.ForeignKey(PlatformApplications, on_delete=models.PROTECT, related_name='platform_score', verbose_name='Platform')
    cohort = models.ForeignKey(CohortApplications, on_delete=models.PROTECT, related_name='cohort_score', verbose_name='Cohort')
    # Values
    r2 = models.FloatField(verbose_name='R2', null=False)
    hr = models.FloatField(verbose_name='Hazard Ratio', null=False)
    hr_ci = DecimalRangeField(verbose_name='Hazard Ratio Confidence Interval', null=True)
    fdr = models.FloatField(verbose_name='FDR adjusted P-value', null=False)

    @property
    def values_dict(self):
        l = {}
        l['R2'] = self.r2
        l['HR'] = self.hr
        if self.hr_ci != None:
            l['HR_lower'] = float(self.hr_ci.lower)
            l['HR_upper'] = float(self.hr_ci.upper)
        l['FDR'] = self.fdr
        return l

# Downloads ?