import requests
from django.db import IntegrityError, transaction
from imports.generic_model import GenericData
from omicspred.models import Publication


class PublicationData(GenericData):

    def __init__(self,pmid):
        GenericData.__init__(self)
        self.pmid = int(pmid)
        self.check_model_exist()
        if not self.model:
            self.fetch_publication_information()


    def check_model_exist(self):
        '''
        Check if a Publication model already exists.
        '''
        try:
            publication = Publication.objects.get(pmid=self.pmid)
            self.model = publication
        except Publication.DoesNotExist:
            self.model = None


    def rest_api_call_to_epmc(self,query):
        '''
        REST API call to EuropePMC
        - query: the search query
        Return type: JSON
        '''
        payload = {'format': 'json'}
        payload['query'] = query
        result = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search', params=payload)
        result = result.json()
        if result:
            result = result['resultList']['result'][0]
            return result
        else:
            print("Can't retrieve publication information from EuropePMC")
            exit(1)


    def fetch_publication_information(self):
        result = self.rest_api_call_to_epmc(f'ext_id:{self.pmid}')
        if result:
            firstauthor = result['authorString'].split(',')[0]
            authors = result['authorString']
            title = result['title'].strip()
            date_publication = result['firstPublicationDate']
            doi = result['doi']
            print(f"# firstauthor: {firstauthor}")
            print(f"# authors: {authors}")
            print(f"# title: {title}")
            print(f"# date_publication: {date_publication}")
            print(f"# DOI: {doi}")
            if result['pubType'] == 'preprint':
                journal = result['bookOrReportDetails']['publisher']
            else:
                journal = result['journalTitle']
            print(f"# journal: {journal}")
            self.data = {
                'pmid': self.pmid,
                'firstauthor': firstauthor,
                'authors': authors,
                'title': title,
                'date_publication': date_publication,
                'journal': journal,
                'doi': doi
            }
        else:
            print(f'Can\'t find a result on EuropePMC for the publication: {self.pmid}')


    @transaction.atomic
    def create_model(self):
        '''
        Retrieve/Create an instance of the Publication model.
        Return type: Publication model
        '''
        try:
            with transaction.atomic():
                self.check_model_exist()
                if not self.model:
                    self.model = Publication()
                    self.model.set_publication_ids(self.next_id_number(Publication, 'num'))
                    for field, val in self.data.items():
                        setattr(self.model, field, val)
                    self.model.save()
        except IntegrityError as e:
            self.model = None
            print(f'Error with the creation of the Publication: {e}')

        return self.model