from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import datetime

class Publication(models.Model):
    """ Class for publications with OmicsPred """
    pmid = models.IntegerField('PubMed ID (PMID)', null=False)

    # Key information (also) in the spreadsheet
    doi = models.CharField('digital object identifier (doi)', max_length=100)

    journal = models.CharField('Journal Name', max_length=100)
    firstauthor = models.CharField('First Author', max_length=50)

    # Information extracted from EuropePMC
    authors = models.TextField('Authors')
    title = models.TextField('Title')
    date_publication = models.DateField('Publication Date')

    date_released = models.DateField('OmicsPred Release Date', null=True, db_index=True)

    # Curation information
    CURATION_STATUS_CHOICES = [
        ('C',  'Curated'),
        ('ID', 'Curated - insufficient data'),
        ('IP', 'Curation in Progress'),
        ('AW', 'Awaiting Curation'),
        ('E',  'Embargoed')
    ]
    curation_status = models.CharField(max_length=2,
                            choices=CURATION_STATUS_CHOICES,
                            default='AW',
                            verbose_name='Curation Status'
                            )
    curation_notes = models.TextField('Curation Notes', default='')

    # Methods
    def __str__(self):
        return f'{self.firstauthor} | PMID:{self.pmid}'

    class Meta:
        get_latest_by = 'id'

    # @property
    # def is_preprint(self):
    #     return 'bioRxiv' in self.journal or 'medRxiv' in self.journal

    @property
    def pub_year(self):
        # Dependant on the context, sometimes the date_publication is returned as a string
        pub_date = self.date_publication
        if type(pub_date) == str:
            pub_date = datetime.strptime(pub_date, '%Y-%m-%d')
        return pub_date.strftime('%Y')


class Cohort(models.Model):
    """ Class to describe cohorts used in samples """
    name_short = models.CharField('Cohort Short Name', max_length=100, db_index=True)
    name_full = models.CharField('Cohort Full Name', max_length=1000)
    name_others = models.TextField('Previous/other/additional names (e.g. sub-cohorts)', null=True)
    url = models.CharField('Cohort URL', max_length=100)

    def __str__(self):
        return self.name_short


class Platform(models.Model):
    """ Class to describe the platform used to get the omics data """
    name = models.CharField('Platform name', max_length=100)
    full_name = models.CharField('Platform full name', max_length=100)
    version = models.CharField('Platform version', max_length=50)
    technic = models.CharField('Platform technic', max_length=100)
    type = models.CharField('Platform type', max_length=100)

    @property
    def scores_count(self):
        return self.platform_score.count()


class EFO(models.Model):
    """ Class to store EFO entries """
    id = models.CharField('EFO ID', max_length=30, primary_key=True)
    label = models.CharField('EFO Label', max_length=500, db_index=True)
    description = models.TextField('EFO Description', null=True)
    url = models.CharField('EFO URL', max_length=500)
    type = models.CharField('Entry type', max_length=100, null=True)

    child_efos = models.ManyToManyField('self', verbose_name='Children EFO', symmetrical=False, related_name='parent_efos')


class PlatformAdditional(models.Model):
    """ Class providing additional information to the Platform """
    publication = models.ForeignKey(Publication, on_delete=models.PROTECT, related_name='platforms', verbose_name='Publication')
    platform = models.ForeignKey(Platform, on_delete=models.PROTECT, related_name='platform_pp', verbose_name='Platform')
    omics_count = models.IntegerField('Omics Entities count', null=False)
    omics_type = models.CharField('Omics type', max_length=50)
    tissue = models.ForeignKey(EFO, on_delete=models.PROTECT, related_name='tissue_platform', verbose_name='Tissue', null=True) # EFO trait defining the sampled tissue
    cohorts = models.ManyToManyField(Cohort, verbose_name='Cohort(s)', related_name='cohort_platform')


class Sample(models.Model):
    """Class to describe samples used in variant associations and PGS training/testing"""

    # Sample Information
    platform_version = models.CharField('Platform version', max_length=50)
    tissue_name = models.CharField('Tissue name', max_length=100, null=True)

    ## Numbers
    sample_number = models.IntegerField('Number of Individuals', null=True)
    # sample_cases = models.IntegerField('Number of Cases', null=True)
    # sample_controls = models.IntegerField('Number of Controls', null=True)
    sample_percent_male = models.FloatField('Percent of Participants Who are Male', validators=[MinValueValidator(0), MaxValueValidator(100)], null=True)
    sample_age = models.FloatField('Sample Age', null=True)
    sample_age_sd = models.FloatField('Mean standard deviation of Age', null=True)


    ## Ancestry
    ancestry_broad = models.CharField('Broad Ancestry Category', max_length=250)
    ancestry_free = models.TextField('Ancestry (e.g. French, Chinese)', null=True)
    ancestry_country = models.TextField('Country of Recruitment', null=True)
    ancestry_additional = models.TextField('Additional Ancestry Description', null=True)

    ## Cohorts/Sources
    source_gwas_catalog = models.CharField('GWAS Catalog Study ID (GCST...)', max_length=20, null=True)
    source_pmid = models.IntegerField('Source PubMed ID (PMID)', null=True)
    source_doi = models.CharField('Source DOI', max_length=100, null=True)
    cohorts = models.ManyToManyField(Cohort, verbose_name='Cohort(s)')
    cohorts_additional = models.TextField('Additional Sample/Cohort Information', null=True)

    curation_notes = models.TextField('Curation Notes', default='')

    def __str__(self):
        s = 'Sample {}'.format(str(self.pk))
        if self.ancestry_broad:
            s += ' - {}'.format(self.ancestry_broad)
        s += ' '+str(self.display_sample_number_total)
        return s


    def list_cohortids(self):
        return [x.name_short for x in self.cohorts.all()]

    @property
    def sample_cases_percent(self):
        if self.sample_cases != None:
            percent = (self.sample_cases / self.sample_number) * 100
            return round(percent,2)
        else:
            return None

    @property
    def display_samples(self):
        sinfo = [common.individuals_format(self.sample_number)]
        if self.sample_cases != None:
            sstring = '[ {:,} cases'.format(self.sample_cases)
            if self.sample_controls != None:
                sstring += ', {:,} controls'.format(self.sample_controls)
            sstring += ' ]'
            sinfo.append(sstring)
        if self.sample_percent_male != None:
            sinfo.append('%s %% Male samples'%str(round(self.sample_percent_male,2)))
        return sinfo

    @property
    def display_samples_for_table(self):
        div_id = "sample_"+str(self.pk)
        sstring = ''
        if self.sample_cases != None:
            sstring += '<div><a class="toggle_table_btn pgs_btn_plus pgs_helptip" id="{}" title="Click to show/hide the details">{}</a></div>'.format(div_id,common.individuals_format(self.sample_number))
            sstring += '<div class="toggle_list" id="list_'+div_id+'">'
            sstring += '<span class="only_export">[</span>'
            sstring += '<ul>\n<li>{:,} cases</li>\n'.format(self.sample_cases)
            if self.sample_controls != None:
                sstring += '<li><span class="only_export">, </span>'
                sstring += '{:,} controls</li>'.format(self.sample_controls)
            sstring += '</ul>'
            sstring += '<span class="only_export">]</span>'
            sstring += '</div>'
        else:
            sstring += self.display_sample_number_total
        if self.sample_percent_male != None:
            sstring += '<span class="only_export">, </span>'
            sstring += '<div class="mt-2 smaller-90">%s %% Male samples</div>'%str(round(self.sample_percent_male,2))
        return sstring

    @property
    def display_sample_number_total(self):
        ssinfo = 'NR'
        if self.sample_number != None:
            # ssinfo = common.individuals_format(self.sample_number)
            ssinfo = self.sample_number
        return ssinfo

    @property
    def display_sample_number_detail(self):
        sinfo = []
        if self.sample_cases != None:
            sinfo.append('<div class="sample_cases">{:,} cases ({}%)</div>'.format(self.sample_cases, self.sample_cases_percent))
            if self.sample_controls != None:
                sinfo.append('<div class="sample_controls">{:,} controls</div>'.format(self.sample_controls))
        if self.sample_percent_male != None:
            sinfo.append('<div class="sample_male">%s%% Male samples</div>'%str(round(self.sample_percent_male,2)))
        return sinfo

    @property
    def display_sample_category_number(self):
        data = []
        if self.sample_cases != None:
            data.append({'name': 'Cases', 'value': self.sample_cases})
            if self.sample_controls != None:
                data.append({'name': 'Controls', 'value': self.sample_controls})
        return data

    @property
    def display_sample_gender_percentage(self):
        data = []
        if self.sample_percent_male != None:
            percent_male = round(self.sample_percent_male,2)
            data = [
                { 'name': '% Male', 'value': percent_male },
                { 'name': '% Female', 'value': round(100-percent_male,2) }
            ]
        return data

    @property
    def display_sources(self):
        d = {}
        if self.source_GWAS_catalog:
            d['GCST'] = self.source_GWAS_catalog
        if self.source_PMID:
            d['PMID'] = self.source_PMID
        if self.source_DOI:
            d['DOI'] = self.source_DOI
        return d

    @property
    def display_ancestry(self):
        if self.ancestry_free in ['NR', '', None]:
            return self.ancestry_broad
        else:
            return '{}<br/><small>({})</small>'.format(self.ancestry_broad, self.ancestry_free)

    @property
    def display_ancestry_inline(self):
        if self.ancestry_free in ['NR', '', None]:
            return self.ancestry_broad
        else:
            return '{} <small>({})</small>'.format(self.ancestry_broad, self.ancestry_free)


class Omics(models.Model):
    """ Generic Class to describe an Omics entity """
    name = models.CharField('Omics entity name', max_length=100, null=True)
    external_id = models.CharField('External ID', max_length=100, db_index=True, null=True)
    external_id_source = models.CharField('External ID Source', max_length=100, null=True)

    class Meta:
        abstract = True


class Gene(Omics):
    """ Class to describe Gene entity """
    synonyms = models.JSONField('Gene synonyms', null=True)
    biotype = models.CharField('Gene biotype', max_length=100, null=True)
    retired_gene_model = models.BooleanField('Retired Gene ID/model', default=False)

    @property
    def scores_count(self):
        return self.gene_score.count()


class Transcript(Omics):
    """ Class to describe Transcript entity """
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE, verbose_name='Associated Gene', related_name="gene_transcript", null=True)
    biotype = models.CharField('Gene biotype', max_length=100, null=True)

    @property
    def scores_count(self):
        return self.transcript_score.count()


class Protein(Omics):
    """ Class to describe Transcript entity """
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE, verbose_name='Associated Gene', related_name="gene_protein", null=True)

    @property
    def scores_count(self):
        return self.protein_score.count()


class Pathway(Omics):
    """ Class to describe Pathway entity """


class Metabolite(Omics):
    """ Class to describe Metabolite entity """
    pathway_group = models.ForeignKey(Pathway, on_delete=models.CASCADE, verbose_name='Associated Pathway Group', related_name="pathway_group_metabolite", null=True)
    pathway_subgroup = models.ForeignKey(Pathway, on_delete=models.CASCADE, verbose_name='Associated Pathway Subgroup', related_name="pathway_subgroup_metabolite", null=True)

    @property
    def scores_count(self):
        return self.metabolite_score.count()


class Score(models.Model):
    """ Class for individual OmicsPred Score (OPGS) """

    # Stable identifiers
    num = models.IntegerField('OmicsPred Number', primary_key=True)
    id = models.CharField('OmicsPred ID', max_length=30, db_index=True)

    name = models.CharField('OmicsPred Name', max_length=100, null=True)

    # Trait information
    trait_reported = models.TextField('Reported Trait')
    trait_additional = models.TextField('Additional Trait Information', null=True)

    # PGS Development/method details
    method_name = models.TextField('Score Development Method')
    method_params = models.TextField('Score Development Details/Relevant Parameters', null=True)

    variants_number = models.IntegerField('Number of Variants', validators=[MinValueValidator(1)])
    variants_interactions = models.IntegerField('Number of Interaction Terms', default=0)
    variants_genomebuild = models.CharField('Original Genome Build', max_length=10, default='NR')


    # Curation/release information
    date_released = models.DateField('OmicsPred Release Date', null=True, db_index=True)
    curation_notes = models.TextField('Curation Notes', default='')

    # Links to related models
    publication = models.ForeignKey(Publication, on_delete=models.PROTECT, related_name='publication_score', verbose_name='Publication')
    platform = models.ForeignKey(Platform, on_delete=models.PROTECT, related_name='platform_score', verbose_name='Platform')
    # efos = models.ManyToManyField(EFO, verbose_name='EFO', related_name='associated_scores')

    ## Omics entities
    genes = models.ManyToManyField(Gene, related_name='gene_score', verbose_name='Gene(s)')
    transcripts = models.ManyToManyField(Transcript, related_name='transcript_score', verbose_name='Transcript(s)')
    proteins = models.ManyToManyField(Protein, related_name='protein_score', verbose_name='Protein(s)')
    metabolites = models.ManyToManyField(Metabolite, related_name='metabolite_score', verbose_name='Metabolite(s)')

    # # LICENSE information/text
    # license = models.TextField('License/Terms of Use', default='''PGS obtained from the Catalog should be cited appropriately, and used in accordance with any licensing restrictions set by the authors. See EBI Terms of Use (https://www.ebi.ac.uk/about/terms-of-use/) for additional details.''')


    # Methods
    def __str__(self):
        if self.name:
            return f'{self.id} | {self.name}'
        else:
            return self.id

    def set_score_ids(self, n):
        self.num = n
        self.id = 'OPGS' + str(n).zfill(6)

    @property
    def performance_data(self):
        data = {}
        for perf in self.score_performance.all():
            for cohort in perf.cohort_metrics.keys():
                data[cohort] = perf.cohort_metrics[cohort]
        return data


class SourceAnnotations(models.Model):
    """ Class to store original annotations """
    score = models.OneToOneField(Score, on_delete=models.PROTECT, related_name='source_annotation_score', verbose_name='OmicsPred Score ID', primary_key=True)
    annotations = models.JSONField('Annotations', default=dict)


class Performance(models.Model):
    """ Class for Performance Metric """
    score = models.ForeignKey(Score, on_delete=models.CASCADE, verbose_name='Score', related_name='score_performance') # \Score that the metrics are associated with
    publication = models.ForeignKey(Publication, on_delete=models.PROTECT, verbose_name='Peformance Source', related_name='publication_performance') # Study that reported performance metrics
    sample = models.ForeignKey(Sample, on_delete=models.PROTECT, verbose_name='Peformance Sample', related_name='sample_performance') # Sample that is associated with
    platform = models.ForeignKey(Platform, on_delete=models.PROTECT, verbose_name='Peformance Platform', related_name='platform_performance') # Platform that is associated with
    efo = models.ForeignKey(EFO, on_delete=models.PROTECT, verbose_name='Peformance EFO', related_name='efo_performance', null=True) # EFO trait that is associated with
    # Evaluation Type
    EVALUATION_CHOICES = [
        ('T',  'Training'),
        ('IV', 'Independent Validation'),
        ('EV', 'External Validation'),
        ('E',  'Evaluation')
    ]
    eval_type = models.CharField(max_length=2,
                            choices=EVALUATION_CHOICES,
                            default='',
                            verbose_name='Evaluation Type'
                            )
    performance_additional = models.TextField('Additional Information', default='')
    source_gwas_catalog = models.CharField('GWAS Catalog Study ID (GCST...)', max_length=20, null=True)
    source_doi = models.CharField('Source DOI', max_length=100, null=True)
    covariates = models.TextField('Covariates Included in the Performance', null=True)
    cohort_label = models.CharField('Cohort label', max_length=100, default='')
    curation_notes = models.TextField('Curation Notes', default='')

    @property
    def associated_opgs_id(self):
        return self.score.id

    @property
    def performance_metrics(self):
        perf_metrics = []

        metrics = self.performance_metric.all()
        if metrics:
            # print(f">> {len(metrics)}")
            for m in metrics:
                # print(f"> {m.name_short}: {m.estimate}")
                # if type(m.estimate) == 'int':
                metric_data = {
                    'type': m.get_performance_type_display(),
                    'name_long': m.name,
                    'name_short': m.name_short,
                    'estimate': m.display_value(m.estimate)
                }
                if m.pvalue:
                    metric_data['p_value'] = m.display_value(m.pvalue)
                perf_metrics.append(metric_data)

        return perf_metrics

    @property
    def cohort_metrics(self):
        cohort_metrics = {}
        #cohort_label = '_'.join([x.name_short for x in self.sample.cohorts.all()])
        cohort_label = self.cohort_label
        metrics = self.performance_metric.all()
        if metrics:
            for m in metrics:
                cohort_metrics[f'{cohort_label}_{m.name_short}'] = {
                    # 'label': f'{cohort_label} {m.name_short}',
                    'estimate': m.display_value(m.estimate)
                }
        return cohort_metrics


class Metric(models.Model):
    """ Class to hold metric type, name, value and confidence intervals of a performance metric """
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE, verbose_name='PGS Performance Metric (PPM)', related_name="performance_metric")

    TYPE_CHOICES = [
        ('PC', "Pearson's correlation"),
        ('SC', "Spearman's rank correlation")
    ]
    performance_type = models.CharField(max_length=40,
        choices=TYPE_CHOICES,
        default='Performance Type',
        db_index=True
    )
    name = models.CharField(verbose_name='Performance Metric Name', max_length=100, null=False) # ex: " Rho score"
    name_short = models.CharField(verbose_name='Performance Metric Name (Short)', max_length=20, null=True) # ex: "Rho"
    source = models.CharField(verbose_name='Performance Metric  Source', max_length=100, null=True)

    estimate = models.FloatField(verbose_name='Estimate', null=False)
    pvalue = models.FloatField(verbose_name='p-value', null=True)


    def __str__(self):
        s = '{}'.format(self.estimate)

        if (self.name_short):
            return '%s (%s): %s'%(self.name, self.name_short, s)
        else:
            return '%s: %s'%(self.name, s)


    def display_value(self,value):
        # Use the scientific notation
        if (0 < value < 0.00001) or (-0.00001 < value < 0):
            new_value = '{:.2e}'.format(value)
        # Round numbers to 5 numbers max
        else:
            new_value = round(value, 5)
        return new_value
