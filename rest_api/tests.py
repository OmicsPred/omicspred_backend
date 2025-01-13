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
    publications_list = ['36991119','123456']

    platforms_list_proteomics = ['Somalogic','Olink']
    platforms_list_metabolomics = ['Metabolon']
    platforms_list_transcriptomics = ['Illumina RNAseq']
    platforms_list = [*platforms_list_proteomics,*platforms_list_metabolomics,*platforms_list_transcriptomics]
    scores_list = ['OPGS000005','OPGS002385','OPGS003006']
    genes_list = ['FCGR2B']
    proteins_list = ['P31994']
    metabolites_list = ['CHEBI_16113']
    pathways_list = ['R-HSA-191273','R-HSA-198933']
    phenotypes_list = ['555.2','250','278.1']

    index_result_mutliplicity = 2
    index_example = 3

    search_pmid = f'pmid={publications_list[0]}'
    search_platform = f'platform={platforms_list_proteomics[1]}'
    search_cohort = f'cohort={cohorts_list[1]}'
    search_author = f'author=Xu'
    search_opgs_id = f'opgs_id={scores_list[0]}'
    search_phenotype = f'phenotype_id={phenotypes_list[0]}'
    search_gene = f'gene={genes_list[0]}'
    seach_mt = f'molecular_trait_id={proteins_list[0]}'
    search_combined = f'{search_opgs_id}&{search_pmid}'

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
        ('Protein/Search', 'protein/search', 1, {'query': [search_gene]}),
        ('Metabolite/Name', 'metabolite', 0, {'path': metabolites_list}),
         # Omics by platform endpoints
        ('Proteomics/Name', 'proteomics',1, {'path': platforms_list_proteomics}),
        ('Metabolomics/Name', 'metabolomics',1, {'path': platforms_list_metabolomics}),
        ('Transcriptomics/Name', 'transcriptomics',1, {'path': platforms_list_transcriptomics}),
        # Performance Metrics endpoints
        ('Performances Search MT','performance/search/protein', 1, {'path': [proteins_list[0]], 'extra_query':search_opgs_id}),
        ('Performances Search','performance/search', 1, {'query': [search_opgs_id,search_pmid,search_platform]}),
        # Publication endpoints
        ('Publications', 'publication/all', 1),
        ('Publications', 'publication/all', 1, {'query': [filter_ids+'='+','.join(publications_list)]}),
        ('Publication/PMID', 'publication', 0, {'path': publications_list}),
        ('Publication Search', 'publication/search', 1, {'query': [search_opgs_id,search_pmid,search_author]}),
        # Sample endpoint
        ('Samples', 'sample/all', 1),
        # Score endpoints
        ('Scores', 'score/all', 1),
        ('Score/ID', 'score', 0, {'path': scores_list}),
        ('Scores Search', 'score/search', 1, {'query': ['opgs_ids='+','.join(scores_list),search_pmid,search_platform,search_cohort]}),
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
        ('Phenotype', 'phenotype', 0, {'path': phenotypes_list}),
        ('Applications - Score', 'applications_score/all', 1),
        ('Applications - Score', 'applications_score', 1, {'path': scores_list}),
        ('Applications - Score Search', 'applications_score/search', 1, {'query': [search_phenotype,search_opgs_id,search_pmid,seach_mt,search_combined]}),
        ('Applications - Sample', 'applications_sample/all', 1),
        # Other endpoints
        ('Info', 'info', 0)
    ]


    endpoints_with_include_flag = [
        (
            'Scores / ancestry', 'score/all', 1,
            {
                'response_path': [],
                'query': ['include_ancestry'],
                'response': ['ancestry']
            }
        ),
        (
            'Score / pathways', f'score/{scores_list[0]}', 1,
            {
                'response_path':['genes',0],
                'query': ['include_pathway'],
                'response': ['pathways']
            }
        ),
        (
            'Scores Search Type / performances', f'score/search/gene/{genes_list[0]}', 1,
            {
                'response_path': [],
                'query': ['include_performance_metrics','include_performance_data'],
                'response': ['score_performance','performance_data']
            }
        ),
        (
            'Scores Search / ancestry', f'score/search', 1,
            {
                'response_path': [],
                'query': [f'{search_pmid}&include_ancestry'],
                'response': ['ancestry']
            }
        ),
        (
            'Metabolomics/Name / performance_metrics', f'metabolomics/{platforms_list_metabolomics[0]}', 1,
            {
                'response_path': [],
                'query': ['include_performance_metrics'],
                'response': ['performance_data']
            }
        ),
        (
            'Proteomics/Name / performance_metrics', f'proteomics/{platforms_list_proteomics[0]}', 1,
            {
                'response_path': [],
                'query': ['include_performance_metrics'],
                'response': ['performance_data']
            }
        ),
        (
            'Transcriptomics/Name / performance_metrics', f'transcriptomics/{platforms_list_transcriptomics[0]}', 1,
            {
                'response_path': [],
                'query': ['include_performance_metrics'],
                'response': ['performance_data']
            }
        ),
        (
            'Pathway / score_counts', f'pathway/all', 1,
            {
                'response_path':['metabolites',0],
                'query': ['include_counts'],
                'response': ['scores_count']
            }
        ),
        (
            'Phenotype / children', f'phenotype/{phenotypes_list[1]}', 0,
            {
                'response_path': [],
                'query': ['include_children'],
                'response': ['child_phenotype']
            }
        )
    ]


    endpoints_with_filter_ids = (
        ('Scores / filter_ids', 'score/all' , scores_list[1:]), # Exclude 1st element
        ('Publications / filter_ids', 'publication/all' , publications_list[1:]), # Exclude 1st element
        ('Applications - Score / filter_ids', 'applications_score/all', scores_list[1:]), # Exclude 1st element
        ('Applications - Sample', 'applications_sample/all', phenotypes_list[1:]) # Exclude 1st element
    )


    def check_response(self,url:str,is_included:int,path_structure:list,included_key:str):
        """ Check that the response contains (or not) the 'included_key' item/data """
        resp = self.client.get(f'{url}={is_included}')
        # Get releavant data content
        content = resp.data
        tmp_content_keys = content.keys()
        if 'results' in tmp_content_keys:
            content = content['results'][0]
        # Browse the data result structure
        for path in path_structure:
            if str(path) == '0':
                content = content[0]
            else:
                content = content[path]
        # Extract the keys of the reached structure
        content_keys = content.keys()
        # Check the presence/absence of the element
        if is_included == 1:
            self.assertIn(included_key, content_keys)
        else:
            self.assertNotIn(included_key, content_keys)


    def check_filter_ids(self,url:str,ids_list:list):
        """ Compare the number of results with the number of IDs provided in the filter_ids parameter """
        ids_list_string = ",".join(ids_list)
        resp = self.client.get(f'{url}?filter_ids={ids_list_string}')
        self.assertEqual(len(resp.data['results']), len(ids_list))


    def send_request(self, url:str):
        """ Send REST API request and check the reponse status code """
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")
        for empty_content in self.empty_resp:
            self.assertNotEqual(content, empty_content)


    def get_empty_response(self, url:str, index:int):
        """ Send REST API request and check the reponse status code """
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode("utf-8"), self.empty_resp[index])


    def get_not_found_response(self, url:str):
        """ Send REST API request on non existing endpoint and check reponse status code """
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)


    def get_paginated_response(self, url:str):
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
                        ex = ex_content[1].split(',')[0] # Only retain first item

                if ex:
                    if re.match(r"^\d+$",ex):
                        url_endpoint += self.fake_examples['integer']
                    elif re.match(r"^\d{4}-\d{2}-\d{2}$", ex):
                        url_endpoint += self.fake_examples['date']
                    else:
                        url_endpoint += self.fake_examples['string']
                    self.get_empty_response(url_endpoint, endpoint[self.index_result_mutliplicity])


    def test_endpoint_not_found(self):
        """ Test an endpoint that doens't exist """
        self.get_not_found_response(self.server+'chocolate')


    def test_endpoint_with_include_flag(self):
        """ Test the 'include flag' used on some of the endpoints """
        for endpoint in self.endpoints_with_include_flag:
            url_endpoint = self.server+endpoint[1]
            query_list = endpoint[self.index_example]['query']
            # Loop over the queries
            for idx, example in enumerate(query_list):
                url = url_endpoint+'?'+example
                response_path = endpoint[self.index_example]['response_path']
                included_key = endpoint[self.index_example]['response'][idx]
                # Test include
                self.check_response(url, 1, response_path, included_key)
                # Test exclude
                self.check_response(url, 0, response_path, included_key)


    def test_endpoint_with_filter_ids_param(self):
        """ Test the 'filter_ids' parameter used on some of the endpoints """
        for endpoint in self.endpoints_with_filter_ids:
            url_endpoint = self.server+endpoint[1]
            self.check_filter_ids(url_endpoint,endpoint[2])