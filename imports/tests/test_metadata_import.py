from django.test import TestCase
from imports.omicspred.parsers.metadata import MetadataTemplate


data_counts = {
    'cohort': 2,
    'dataset': 5,
    'metric': 2,
    'score_performance': 2,
    'sample_performance': 6,
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
sample_data = { # 2nd score entry + Validation
    'sample_number': 1856,
    'sample_percent_male': 45.1,
    'sample_age': 52.5,
    'ancestry_broad': 'European',
    'ancestry_free': 'Finnish',
    'ancestry_country': 'UK'
}
cohort_data = { # 2nd cohort entry
    'name_short': 'UKB',
    'name_full': 'UK Biobank',
    'url': 'https://www.ukbiobank.ac.uk/'
}
performance_data = { # 2nd score entry + Validation
    'eval_type': 'Validation',
    'covariates': '40 PEER Factors; sex; age',
}
metric_data_r2 = { # 2nd score entry + Validatio
    'type': "Pearson's correlation",
    'estimate': 0.48,
    'name': 'Proportion of the variance explained',
    'name_short': 'R2',
    'pvalue': 2.56E-75
}
metric_data_rho = { # 2nd score entry + Validatio
    'type': "Spearman's rank correlation",
    'estimate': 0.66,
    'name': 'Spearman correlation coefficient',
    'name_short': 'Rho'
}
pmid = 36991119

file_loc = './imports/tests/metadata_test.xlsx'

dataset_prefix = 'Test'

species = 'Homo sapiens'

license = 'Creative Commons 4.0 International (CC BY 4.0)'


class ImportMetadataTest(TestCase):
    ''' Test the Metadata import '''

    def __init__(self, methodName = "runTest"):
        super().__init__(methodName)
        self.metadata_template = MetadataTemplate(file_loc,license)


    def parser_data_count(self, parsed_data:dict, type:str):
        self.assertEqual(len(parsed_data.keys()), data_counts[type])


    def parser_data_check(self, parsed_data:dict, example_data:dict):
        data2test = parsed_data.data
        for item in example_data.keys():
            self.assertEqual(data2test[item], example_data[item])


    def nested_parser_data_check(self, parsed_data:dict, example_data:dict, index:int=0):
        data_key = list(parsed_data.keys())[index]
        self.parser_data_check(parsed_data[data_key], example_data)


    def test_metadata_parsing(self):
        ''' Test the code parsing the metadata Excel file '''
        
        self.assertTrue(isinstance(self.metadata_template, MetadataTemplate))

        ## Parsing step ##
        self.metadata_template.read_curation(dataset_prefix)
        
        # Start Parsing tests
        print("\n** Start parsing tests **")

        print("  * Test Species parser")
        self.assertEqual(self.metadata_template.species.name_latin, species)

        print("  * Test Publication parser")
        # Publication
        publication = self.metadata_template.parsed_publication
        self.assertIsNotNone(publication)
        self.assertEqual(publication.pmid, pmid)

        # Scores
        print("  * Test Score parser")
        scores = self.metadata_template.parsed_scores
        self.parser_data_count(scores,'score')
        self.nested_parser_data_check(scores, score_data, 1)
        score_name = list(scores.keys())[1]

        # Molecular traits
        print("  * Test Molecular trait parser")
        score_name_tr = list(scores.keys())[5]
        score_data_mt = self.metadata_template.parsed_scores[score_name_tr]
        molecular_trait = score_data_mt.additional_data['genes'][0]
        self.assertEqual(molecular_trait.external_id, gene_data['external_id'])
        self.assertEqual(molecular_trait.name, gene_data['name'])

        # Cohorts
        print("  * Test Cohort parser")
        cohorts = self.metadata_template.parsed_cohorts
        self.parser_data_count(cohorts,'cohort')
        self.nested_parser_data_check(cohorts, cohort_data, 1)

        # Datasets
        print("  * Test Dataset parser")
        datasets = self.metadata_template.parsed_datasets
        self.parser_data_count(datasets,'dataset')
        dataset_key = list(datasets.keys())[0]
        dataset = datasets[dataset_key]
        
        # Tissue
        print("  * Test Tissue parser")
        self.parser_data_check(dataset.tissue, tissue_data)

        # Platform
        print("  * Test Platform parser")
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
            print("  * Test Sample parser")
            sample = sample_performance['sample']
            self.parser_data_check(sample, sample_data)
            cohorts = sample.data['cohorts']
            self.assertEqual(cohorts[0].name_short, cohort_data['name_short'])
        
            # Performance
            print("  * Test Performance parser")
            performance = sample_performance['performance']
            self.parser_data_check(performance, performance_data)

            # Metrics
            print("  * Test Metric parser")
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

        ## Import step ##
        # Start Import tests
        print("\n** Start import tests **")
        self.parser_data_count(self.metadata_template.parsed_datasets,'dataset')
        # self.assertEqual(len(self.metadata_template.parsed_datasets), )
        self.metadata_template.import_curation()