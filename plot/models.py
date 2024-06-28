from django.db import models

# Create your models here.
class Plot(models.Model):
    pmid = models.IntegerField('PubMed ID (PMID)', null=False)
    platform_name = models.CharField('Platform name', max_length=100, null=False)
    dataset_name = models.CharField('Dataset name', max_length=150, null=True)
    plot_data = models.JSONField('Plot data', default=dict)
    score_data = models.JSONField('Score data', default=dict)