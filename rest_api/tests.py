from rest_framework.test import APITestCase
from django.conf import settings
import re


class BrowseEndpointTest(APITestCase):
    """ Test the REST endpoints """

    # Load data in DB - Must live in the rest_api/fixtures/ directory
    fixtures = ['db_test']
    databases = {'default', 'applications'}

    # Change throttle rates for the tests
    rate4test = '200/min'
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = { 'anon': rate4test, 'user': rate4test }

    # Base URL of the server
    server = '/rest/'

    fake_examples = {'string': 'ABC123CDE', 'integer': '00001', 'date': '1990-01-01'}
    empty_resp = ['{}', '{"size":0,"count":0,"next":null,"previous":null,"results":[]}', '[]']

    # Data example
    filter_ids = 'filter_ids'
    cohorts_list = ['INTERVAL','UKB']
    publications_list = ['36991119']

    platforms_list_proteomics = ['Somalogic','Olink']
    platforms_list_metabolomics = ['Metabolon']
    platforms_list = [*platforms_list_proteomics,*platforms_list_metabolomics]
    scores_list = ['OPGS000005','OPGS002385','OPGS003006']
    genes_list = ['FCGR2B']
    proteins_list = ['P31994']
    metabolites_list = ['CHEBI_16113']
    pathways_list = ['R-HSA-191273','R-HSA-198933']
    phecodes_list = ['555.2','250.2','278.1']

    index_result_mutliplicity = 2
    index_example = 3

    search_pmid = f'pmid={publications_list[0]}'

    # Tuple: ( Endpoint name | Base URL | Flag for results multiplicity | Parameter examples* )
    endpoints = [
        # Cohort endpoints
        ('Cohorts', 'cohort/all', 1),
        ('Cohort/SYMBOL', 'cohort', 0, {'path': cohorts_list}),
        # Pathways
        ('Pathways', 'pathway/all', 1),
        ('Pathways/Name', 'pathway', 0, {'path': pathways_list}),
        # Molecular trait endpoints
        ('Gene/Name', 'gene', 0, {'path': genes_list}),
        ('Protein/Name', 'protein', 0, {'path': proteins_list}),
        ('Protein/Search', 'protein/search', 1, {'query': ['gene='+genes_list[0]]}),
        ('Metabolite/Name', 'metabolite', 0, {'path': metabolites_list}),
         # Omics by platform endpoints
        ('Proteomics/Name', 'proteomics',1, {'path': platforms_list_proteomics}),
        ('Metabolomics/Name', 'metabolomics',1, {'path': platforms_list_metabolomics}),
        # ('Transcriptomics/Name', 'transcriptomics',1, {'path': platforms_list_transcriptomics}),
        # Performance Metrics endpoints
        ('Performances Search MT','performance/search/protein', 1, {'path': [proteins_list[0]], 'extra_query':'opgs_id='+scores_list[0]}),
        ('Performances Search','performance/search', 1, {'query': ['opgs_id='+scores_list[0]]}),
        # Publication endpoints
        ('Publications', 'publication/all', 1),
        ('Publications', 'publication/all', 1, {'query': [filter_ids+'='+','.join(publications_list)]}),
        ('Publication/PMID', 'publication', 0, {'path': publications_list}),
        ('Publication Search', 'publication/search', 1, {'query': ['opgs_id='+scores_list[0],search_pmid]}),
        # Sample endpoint
        ('Samples', 'sample/all', 1),
        # Score endpoints
        ('Scores', 'score/all', 1),
        ('Scores', 'score/all', 1, {'query': [filter_ids+'='+','.join(scores_list)]}),
        ('Score/ID', 'score', 0, {'path': scores_list}),
        ('Scores Search', 'score/search', 1, {'query': [search_pmid]}),
        ('Scores Search Type', 'score/search/protein', 1, {'path': [proteins_list[0]],'extra_query': 'include_performance_metrics=1'}),
        ('Scores Search Type', 'score/search/gene', 1, {'path': [genes_list[0]], 'extra_query': 'include_performance_data=1'}),
        ('Scores Search Type', 'score/search/metabolite', 1, {'path': [metabolites_list[0]]}),
        ('Scores Performance', 'score/performance', 0, {'path': scores_list}),
        # Dataset
        ('Datasets', 'dataset/all', 1),
        ('Dataset/Name', 'dataset', 1, {'path': ['INTERVAL']}),
        ('Dataset Search', 'dataset/search', 1, {'query': [search_pmid]}),
        # Platform endpoints
        ('Platforms', 'platform/all', 1),
        ('Platform/Name', 'platform', 0, {'path': platforms_list}),

        # Applications
        ('Phecode', 'phecode', 0, {'path': phecodes_list}),
        ('Applications - Score', 'applications_score/all', 1),
        ('Applications - Score', 'applications_score', 1, {'path': scores_list}),
        ('Applications - Score Search', 'applications_score/search', 1, {'query': ['phecode_id='+phecodes_list[0],'opgs_id='+scores_list[0]]}),
        ('Applications - Sample', 'applications_sample/all', 1),
        # Other endpoints
        ('Info', 'info', 0)
    ]


    def send_request(self, url):
        """ Send REST API request and check the reponse status code """
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")
        for empty_content in self.empty_resp:
            self.assertNotEqual(content, empty_content)


    def get_empty_response(self, url, index):
        """ Send REST API request and check the reponse status code """
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode("utf-8"), self.empty_resp[index])


    def get_not_found_response(self, url):
        """ Send REST API request on non existing endpoint and check reponse status code """
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)


    def get_paginated_response(self, url):
        """ Send REST API request with limit and offset parameters, and check the reponse status code """
        resp = self.client.get(url+'?limit=20&offset=20')
        self.assertEqual(resp.status_code, 200)


    def test_endpoints(self):
        """ Test the status code of each endpoint """
        for endpoint in self.endpoints:
            url_endpoint = self.server+endpoint[1]

            if len(endpoint) > self.index_example:
                # Endpoint with parameter within the URL path
                if ('path' in endpoint[self.index_example]):
                    for example in endpoint[self.index_example]['path']:
                        request = url_endpoint+'/'+example
                        self.send_request(request)
                        if 'extra_query' in endpoint[self.index_example]:
                            request_2 = request+'?'+endpoint[self.index_example]['extra_query']
                            self.send_request(request_2)
                # Endpoint with parameter as query
                if ('query' in endpoint[self.index_example]):
                    for example in endpoint[self.index_example]['query']:
                        self.send_request(url_endpoint+'?'+example)
            else:
                self.send_request(url_endpoint)
                if endpoint[self.index_result_mutliplicity]:
                    self.get_paginated_response(url_endpoint)


    def test_endpoints_with_slash(self):

        """ Test the status code of each endpoint, with a trailing slash """
        for endpoint in self.endpoints:
            url_endpoint = self.server+endpoint[1]+'/'

            if len(endpoint) > self.index_example:
                # Endpoint with parameter within the URL path
                if ('path' in endpoint[self.index_example]):
                    for example in endpoint[self.index_example]['path']:
                        request = url_endpoint+example+'/'
                        self.send_request(request)
                        if 'extra_query' in endpoint[self.index_example]:
                            request_2 = request+'?'+endpoint[self.index_example]['extra_query']
                            self.send_request(request_2)
                # Endpoint with parameter as query
                if ('query' in endpoint[self.index_example]):
                    for example in endpoint[self.index_example]['query']:
                        self.send_request(url_endpoint+'?'+example)
            else:
                self.send_request(url_endpoint)
                if endpoint[self.index_result_mutliplicity]:
                    self.get_paginated_response(url_endpoint)


    def test_empty_endpoints(self):
        """ Test the status code and empty response of each endpoint listed above """
        for endpoint in self.endpoints:
            url_endpoint = self.server+endpoint[1]+'/'
            ex = None

            if len(endpoint) > self.index_example:
                # Endpoint with parameter within the URL path
                if ('path' in endpoint[self.index_example]):
                    ex = endpoint[self.index_example]['path'][0]

                    # Endpoint with parameter as query
                if ('query' in endpoint[self.index_example]):
                        ex_full = endpoint[self.index_example]['query'][0]
                        ex_content = ex_full.split('=')
                        url_endpoint += '?'+ex_content[0]+'='
                        ex = ex_content[1]

                if ex:
                    if re.match("^\d+$",ex):
                        url_endpoint += self.fake_examples['integer']
                    elif re.match("^\d{4}-\d{2}-\d{2}$", ex):
                        url_endpoint += self.fake_examples['date']
                    else:
                        url_endpoint += self.fake_examples['string']
                    self.get_empty_response(url_endpoint, endpoint[self.index_result_mutliplicity])


    def test_endpoint_not_found(self):
        """ Test an endpoint that doens't exist """
        self.get_not_found_response(self.server+'chocolate')
