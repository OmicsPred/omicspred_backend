import pandas as pd
import numpy as np
import requests


class GWASParser():

    def __init__(self, filepaths):
        self.filepaths = filepaths
        self.data = {}


    def parse_files(self):
        for filepath in self.filepaths:
            df = pd.read_csv(filepath)
            print(f"  > FILE: {filepath}")
            for index, row in df.iterrows():
                gcst_id = None
                pmid = None

                # Platform info
                platform = row['Platform']
                if platform not in self.data.keys():
                    self.data[platform] = {}
                # Cohort
                if 'Cohort' in row.keys():
                    cohort = row['Cohort']
                else:
                    cohort = 'Internal' # INTERVAL
                self.data[platform][cohort] = {}
                # Covariantes info
                covariates = row['Covariates adjustment (by linear regression)']
                if covariates and covariates not in [None,np.nan,'nan','']:
                    self.data[platform][cohort]['covariates'] = covariates
                # DOI -> PMID
                doi = row['Reference (DOI)'].split('\n')[0]
                if doi == 'current manuscript' or doi == 'Current manuscript':
                    doi = '10.1038/s41586-023-05844-9'
                else:
                    doi = doi.replace('https://doi.org/','')
                self.data[platform][cohort]['doi'] = doi

                # PMID -> GCST ID
                pmid = self.get_pmid_from_epmc(doi)
                if pmid:
                    gcst_id = self.get_gcst_id(pmid)
                if gcst_id:
                    self.data[platform][cohort]['gcst_id'] = gcst_id
                # print(f"\nCohort: {cohort} | Platform {platform} | DOI: {doi} | PMID: {pmid} | GCST: {gcst_id}")
                # print(f"  > Covariates {self.data[platform][cohort]['covariates']}")




    def get_pmid_from_epmc(self, doi):
        payload = {'format': 'json'}
        query = f'doi:{doi}'
        payload['query'] = query
        result = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search', params=payload)
        result = result.json()
        results_list = result['resultList']['result']
        if results_list:
            result = results_list[0]
            if result['pubType'] != 'preprint':
                if 'pmid' in result:
                    return result['pmid']
        else:
            return None

    def get_gcst_id(self,pmid):
        result = requests.get(f'https://www.ebi.ac.uk/gwas/rest/api/studies/search/findByPublicationIdPubmedId?pubmedId={pmid}')
        result = result.json()
        results_list = result['_embedded']['studies']
        if results_list:
            result = results_list[0]
            if result['accessionId']:
                return result['accessionId']
        else:
            return None
