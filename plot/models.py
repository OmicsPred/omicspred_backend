from django.db import models

# Create your models here.
class Plot(models.Model):
    publication_id = models.CharField('Publication ID (OPP)', max_length=20, db_index=True)
    pmid = models.IntegerField('PubMed ID (PMID)', null=False)
    platform_name = models.CharField('Platform name', max_length=100, null=False)
    dataset_id = models.CharField('Dataset ID (OPD)', max_length=20, db_index=True)
    dataset_name = models.CharField('Dataset name', max_length=150, null=True)
    plot_data = models.JSONField('Plot data', default=dict)
    score_data = models.JSONField('Score data', default=dict)