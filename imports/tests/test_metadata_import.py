from django.test import TestCase
from imports.omicspred.parsers.metadata import MetadataTemplate
from imports.tests.config import *
from omicspred.models import *


data_counts = {
    'cohort': 2,
    'dataset': 5,
    'metric': 2,
    'performance': 12,
    'platform': 5,
    'sample': 11,
    'sample_performance': 6,
    'score_dataset': 2,
    'score_performance': 2,
    'score': 6
}
score_data = { # 2nd score entry
    'name': 'genetic_score_e_selectine',
    'trait_reported': 'E-selectin',
    'trait_reported_id': 'P16581',
    'method_name': 'Bayesian Ridge regression',
    'method_params': 'LD/SNP r2 threshold',
    'variants_genomebuild': 'GRCh38',
    'variants_number': 121
}
platform_data = { # 2nd score entry
    'name': 'Olink',
    'version': 'Explore',
}
tissue_data = { # 2nd score entry
    'id': 'UBERON_0001969',
    'label': 'blood plasma',
}
gene_data = {
    'external_id': 'ENSG00000113303',
    'name': 'BTNL8'
}
sample_data = { # 2nd score entry + External Validation
    'sample_number': 1856,
    'sample_percent_male': 45.1,
    'sample_age': 52.5,
    'sample_age_sd': 6.4,
    'ancestry_broad': 'European',
    'ancestry_free': 'Finnish',
    'ancestry_country': 'UK'
}
cohort_data = { # 2nd cohort entry
    'name_short': 'UKB',
    'name_full': 'UK Biobank',
    'url': 'https://www.ukbiobank.ac.uk/'
}
performance_data_parser = { # 2nd score entry + External Validation
    'eval_type': 'External Validation',
    'covariates': '40 PEER Factors; sex; age',
}
performance_data_import = { # 2nd score entry + External Validation
    'eval_type': 'EV',
    'covariates': '40 PEER Factors; sex; age',
}
metric_data_r2 = { # 2nd score entry + External Validation
    'type': "Pearson's correlation",
    'estimate': 0.48,
    'name': 'Proportion of the variance explained',
    'name_short': 'R2',
    'pvalue': 2.56E-75
}
metric_data_rho = { # 2nd score entry + External Validation
    'type': "Spearman's rank correlation",
    'estimate': 0.66,
    'name': 'Spearman correlation coefficient',
    'name_short': 'Rho'
}
pmid = 36991119


class ImportMetadataTest(TestCase):
    ''' Test the Metadata import '''

    def __init__(self, methodName = "runTest"):
        super().__init__(methodName)
        # Variables used from 'imports.tests.config' module
        self.metadata_template = MetadataTemplate(file_loc,platform_types,license,species)


    def parser_data_count(self, parsed_data:dict, type:str):
        self.assertEqual(len(parsed_data.keys()), data_counts[type])


    def parser_data_check(self, parsed_data:dict, example_data:dict):
        ''' Compare the attributes from the data example with the content of the parser "data" '''
        data2test = parsed_data.data
        for item in example_data.keys():
            if isinstance(example_data[item], float):
                self.assertEqual(float(data2test[item]), float(example_data[item]))
            else:
                self.assertEqual(data2test[item], example_data[item])

    def nested_parser_data_check(self, parsed_data:dict, example_data:dict, index:int=0):
        data_key = list(parsed_data.keys())[index]
        self.parser_data_check(parsed_data[data_key], example_data)


    def import_data_check(self, imported_data:object, example_data:dict):
        ''' Compare the attributes from the data example with the object attributes '''
        for item in example_data.keys():
            self.assertEqual(getattr(imported_data, item), example_data[item])


    def print_test_header(self, entity:str, test_type:str):
        print(f"  * Test {entity} {test_type}")


    def test_metadata_parsing(self):
        ''' Test the code parsing the metadata Excel file '''
        test_type = 'parser'
        self.assertTrue(isinstance(self.metadata_template, MetadataTemplate))

        ## Parsing step ##
        self.metadata_template.read_curation(dataset_prefix)
        
        # Start Parsing tests
        print("\n** Start parsing tests **")

        # Species
        self.print_test_header('Species', test_type)
        self.assertEqual(self.metadata_template.species.name_latin, species)

        # Publication
        self.print_test_header('Publication', test_type)
        publication = self.metadata_template.parsed_publication
        self.assertIsNotNone(publication)
        self.assertEqual(publication.pmid, pmid)

        # Scores
        self.print_test_header('Score', test_type)
        scores = self.metadata_template.parsed_scores
        self.parser_data_count(scores,'score')
        self.nested_parser_data_check(scores, score_data, 1)
        score_name = list(scores.keys())[1]

        # Molecular traits
        self.print_test_header('Molecular trait', test_type)
        score_name_tr = list(scores.keys())[5]
        score_data_mt = self.metadata_template.parsed_scores[score_name_tr]
        molecular_trait = score_data_mt.additional_data['genes'][0]
        self.assertEqual(molecular_trait.external_id, gene_data['external_id'])
        self.assertEqual(molecular_trait.name, gene_data['name'])

        # Cohorts
        self.print_test_header('Cohort', test_type)
        cohorts = self.metadata_template.parsed_cohorts
        self.parser_data_count(cohorts,'cohort')
        self.nested_parser_data_check(cohorts, cohort_data, 1)

        # Datasets
        self.print_test_header('Dataset', test_type)
        datasets = self.metadata_template.parsed_datasets
        self.parser_data_count(datasets,'dataset')
        dataset_key = list(datasets.keys())[0]
        dataset = datasets[dataset_key]
        
        # Tissue
        self.print_test_header('Tissue', test_type)
        self.parser_data_check(dataset.tissue, tissue_data)

        # Platform
        self.print_test_header('Platform', test_type)
        self.parser_data_check(dataset.platform, platform_data)

        # Samples / Performance Metricss
        sample_performances = self.metadata_template.parsed_sample_performance
        self.parser_data_count(sample_performances,'sample_performance')
        self.assertIn(score_name, sample_performances.keys())
        if score_name in sample_performances.keys():
            score_sp_list = sample_performances[score_name]
            self.assertEqual(len(score_sp_list), data_counts['score_performance'])
            sample_performance = score_sp_list[1]

            # Sample
            self.print_test_header('Sample', test_type)
            sample = sample_performance['sample']
            self.parser_data_check(sample, sample_data)
            cohorts = sample.data['cohorts']
            self.assertEqual(cohorts[0].name_short, cohort_data['name_short'])
        
            # Performance
            self.print_test_header('Performance', test_type)
            performance = sample_performance['performance']
            self.parser_data_check(performance, performance_data_parser)

            # Metrics
            self.print_test_header('Metric', test_type)
            metrics = performance.metrics
            self.assertEqual(len(metrics), data_counts['metric'])
            print("    - Test Metric parser R2")
            self.parser_data_check(metrics[0], metric_data_r2)
            print("    - Test Metric parser Rho")
            self.parser_data_check(metrics[1], metric_data_rho)
        
        ## Import step ##
        self.metadata_import()


    def metadata_import(self):
        ''' Test the code importing the parsed metadata into a database '''
        test_type = 'import'
        ## Import step ##
        # Start Import tests
        print("\n** Start data import **")
        self.parser_data_count(self.metadata_template.parsed_datasets,'dataset')
        self.metadata_template.import_curation()

        print("\n** Start import tests **")

        # Species
        self.print_test_header('Species', test_type)
        species_model = Species.objects.get(name_latin=species)
        self.assertIsInstance(species_model, Species)
        self.assertEqual(species_model.name_latin, species)

        # Publication
        self.print_test_header('Publication', test_type)
        publication_model = Publication.objects.get(pmid=pmid)
        self.assertIsInstance(publication_model, Publication)
        self.assertEqual(publication_model.pmid, pmid)

        # Scores
        self.print_test_header('Score', test_type)
        scores_count = Score.objects.count()
        self.assertEqual(scores_count, data_counts['score'])

        score_model = Score.objects.get(name=score_data['name'])
        self.assertIsInstance(score_model, Score)
        self.import_data_check(score_model, score_data)

        # Molecular traits
        self.print_test_header('Molecular trait', test_type)
        gene_model = Gene.objects.get(name=gene_data['name'])
        self.assertIsInstance(gene_model, Gene)
        self.import_data_check(gene_model, gene_data)

        # Cohorts
        self.print_test_header('Cohort', test_type)
        cohorts_count = Cohort.objects.count()
        self.assertEqual(cohorts_count, data_counts['cohort'])
        cohort_model = Cohort.objects.get(name_short=cohort_data['name_short'])
        self.import_data_check(cohort_model, cohort_data)

        # Platform
        self.print_test_header('Platform', test_type)
        platforms_count = Platform.objects.count()
        self.assertEqual(platforms_count, data_counts['platform'])
        platform_model = Platform.objects.get(name=platform_data['name'], version=platform_data['version'])
        self.assertIsInstance(platform_model, Platform)

        # Tissue
        self.print_test_header('Tissue', test_type)
        tissue_model = EFO.objects.get(id=tissue_data['id'])
        self.assertIsInstance(tissue_model, EFO)
        self.import_data_check(tissue_model, tissue_data)

        # Datasets
        self.print_test_header('Dataset', test_type)
        datasets_count = Dataset.objects.count()
        self.assertEqual(datasets_count, data_counts['dataset'])
        dataset_model = Dataset.objects.get(
            platform=platform_model,
            publication=publication_model,
            tissue=tissue_model,
            license=license
        )
        self.assertIsInstance(dataset_model, Dataset)
        scores_dataset_count = Score.objects.filter(dataset=dataset_model).count()
        self.assertEqual(scores_dataset_count, data_counts['score_dataset'])

        # Sample
        self.print_test_header('Sample', test_type)
        samples_count = Sample.objects.count()
        self.assertEqual(samples_count, data_counts['sample'])
        sample_model = Sample.objects.get(sample_number=sample_data['sample_number'], sample_age_sd=sample_data['sample_age_sd'])
        self.assertIsInstance(sample_model, Sample)
        self.import_data_check(sample_model, sample_data)
        sample_cohorts = sample_model.cohorts.all()
        self.assertEqual(sample_cohorts[0], cohort_model)

        # Performance
        self.print_test_header('Performance', test_type)
        performances_count = Performance.objects.count()
        self.assertEqual(performances_count, data_counts['performance'])
        performance_models = score_model.score_performance.all()
        self.assertEqual(len(performance_models), data_counts['score_performance'])
        performance_model = None
        for perf_model in performance_models:
            if perf_model.eval_type == performance_data_import['eval_type']:
                performance_model = perf_model
                self.import_data_check(performance_model, performance_data_import)
                break
        self.assertIsInstance(performance_model, Performance)

        # Metrics
        self.print_test_header('Metric', test_type)
        metric_models = performance_model.performance_metric.all()
        self.assertEqual(len(metric_models), data_counts['metric'])
        for metric_model in metric_models:
            if metric_model.name_short == metric_data_r2['name_short']:
                self.import_data_check(metric_model, metric_data_r2)
            else:
                self.import_data_check(metric_model, metric_data_rho)