from imports.omicspred.parsers.gwas import GWASParser
from imports.omicspred.parsers.summary import SummaryParser
from imports.omicspred.parsers.rnaseq import RNAseqParser
from imports.omicspred.parsers.protein import ProteinParser
from imports.omicspred.parsers.metabolite import MetaboliteParser
from imports.omicspred.parsers.data_content import *
from omicspred.models import Publication, Platform


genomebuild = 'GRCh37'

def add_publication():

    pmid = 36991119
    try:
        publication = Publication.objects.get(pmid=pmid)
    except Publication.DoesNotExist:
        publication = Publication()
        publication.pmid = 36991119
        publication.doi = '10.1038/s41586-023-05844-9'
        publication.firstauthor = 'Xu Y'
        publication.authors = 'Xu Y, Ritchie SC, Liang Y, Timmers PRHJ, Pietzner M, Lannelongue L, Lambert SA, Tahir UA, May-Wilson S, Foguet C, Johansson Å, Surendran P, Nath AP, Persyn E, Peters JE, Oliver-Williams C, Deng S, Prins B, Luan J, Bomba L, Soranzo N, Di Angelantonio E, Pirastu N, Tai ES, van Dam RM, Parkinson H, Davenport EE, Paul DS, Yau C, Gerszten RE, Mälarstig A, Danesh J, Sim X, Langenberg C, Wilson JF, Butterworth AS, Inouye M.'
        publication.journal = 'Nature'
        publication.title = 'An atlas of genetic scores to predict multi-omic traits.'
        publication.date_publication = '2023-03-29'
        publication.save()
    return publication


def add_platform(platform_name,platform_type,extra_data):
    try:
        platform = Platform.objects.get(name__iexact=platform_name, type__iexact=platform_type)
    except Platform.DoesNotExist:
        platform = Platform()
        platform.name = platform_name
        platform.type = platform_type
        if 'version' in extra_data.keys():
            platform.version = extra_data['version']
        if 'full_name' in extra_data.keys():
            platform.full_name = extra_data['full_name']
        if 'technic' in extra_data.keys():
            platform.technic = extra_data['technic']
        platform.save()
    return platform

def run():

    path = '/Users/lg10/Workspace/git/clone/OmicsPred_bak/src/data'

    print("# Fetch GWAS data")
    gwas_files = [f'{path}/paper_data/supplementary_tables_gwas.csv',f'{path}/paper_data/supplementary_tables_qc.csv']
    gwas_data = GWASParser(gwas_files)
    gwas_data.parse_files()
    #
    # print(f">> GWAS DATA:\n{gwas_data.data}")


    publication = add_publication()

    for study in studies.keys():
        print(f'\n\n##### {study} #####\n')
        # Summary
        summary_info = { 'name': study, 'filepath': f'{path}/{study}/sumarry.json'}
        summary = SummaryParser(summary_info, studies[study]['sample_cohort_info'])
        summary.parse_summary_file()
        samples_info = summary.import_to_database()
        # continue

        # Data
        platform = study.split('_',1)[1]
        filename = study.split('_')[-1]
        type = study.split('_')[0]
        platform_model = add_platform(platform.replace('_',' '),type, studies[study])
        data_info = {
            'name': study,
            'study_info': studies[study],
            'gwas_data': gwas_data,
            'type': type,
            'platform': platform_model,
            'protein_platform': protein_platform,
            'filepath': f'{path}/paper_data/{filename}.csv',
            'samples_info': samples_info,
            'publication': publication,
            'genomebuild': genomebuild
        }
        if study.startswith('Transcriptomics'):
            rnaseq = RNAseqParser(data_info)
            rnaseq.parse_data()
        elif study.startswith('Proteomics'):
            protein = ProteinParser(data_info)
            protein.parse_data()
        elif study.startswith('Metabolomics'):
            metabolite = MetaboliteParser(data_info)
            metabolite.parse_data()
