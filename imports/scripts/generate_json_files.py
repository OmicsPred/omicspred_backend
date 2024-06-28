import requests
import time
import json
# from functools import reduce
# import operator
# from django.db.models import Q
# from plot.models import Plot


studies = {
    36991119: {
        'Nightingale': [],
        'Metabolon': [],
        'Olink': ['INTERVAL'],
        'Somalogic': [],
        'Illumina RNAseq': []
    },
    12345: {
        'Olink': ['UKB European','UKB Multi-ancestry']
    }
}

url_root = 'http://127.0.0.1:7000/rest'
plot_url_root = f'{url_root}/plot/file/search?format=json&pmid='
plot_score_url_root = f'{url_root}/plot/score/search?format=json&pmid='
table_url_root = f'{url_root}/'
default_path = '/Users/lg10/Workspace/git/fork/omicspred_frontend/public/data/'

def rest_api_call(url,endpoint,parameters=None):
    """"
    Generic method to perform REST API calls to the PGS Catalog
    > Parameters:
        - url: URL to the REST API
        - endpoint: REST API endpoint
        - parameters: extra parameters to the REST API endpoint, if needed
    > Return type: dictionary
    """
    rest_full_url = url+endpoint
    if parameters:
        rest_full_url += parameters

    print("\t\t> URL: "+rest_full_url)
    try:
        response = requests.get(rest_full_url)
        response_json = response.json()
        # Response with pagination
        if 'next' in response_json:
            count_items = response_json['count']
            results = response_json['results']
            # Loop over the pages
            while response_json['next'] and count_items > len(results):
                time.sleep(1)
                response = requests.get(response_json['next'])
                response_json = response.json()
                results = results + response_json['results']
            if count_items != len(results):
                print(f'The number of items are differents from expected: {len(results)} found instead of {count_items}')
        # Respone without pagination
        else:
            results = response_json
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        raise SystemExit(e)
    return results


def fetch_score_data(parameters):
    plot_score_data = rest_api_call(plot_score_url_root, parameters)

    for score in plot_score_data:
        for molecular_trait in ['proteins','genes','transcripts','metabolites']:
            if len(score[molecular_trait]) == 0:
                del score[molecular_trait]
    return plot_score_data


def fetch_plot_data(parameters):
    plot_data = rest_api_call(plot_url_root, parameters)
    return plot_data


def write_data(plot_data, path):
    with open(path, mode="w") as f:
        # f.write(json.dumps(plot_data, indent=4))
        f.write(json.dumps(plot_data))


def run():

    for pmid in studies.keys():
        print(f"# {pmid}:")
        for platform in studies[pmid]:
            platform_name = platform.replace(' ','_')
            print(f"  > {platform_name}")
            parameters = f'{pmid}&platform={platform}'
            datasets = studies[pmid][platform]
            file_path_prefix = f'{default_path}/{pmid}/{platform_name}'
            if len(datasets) > 0:
                for dataset in datasets:

                    dataset_parameters = parameters+'&dataset='+dataset

                    dataset_name = dataset.replace(' ','_')
                    dataset_file_path_prefix = f'{file_path_prefix}_{dataset_name}'

                    # Plot file
                    print(f"\t- Plot data")
                    plot_data = fetch_plot_data(dataset_parameters)
                    plot_file_path = f'{dataset_file_path_prefix}_plot.json'
                    write_data(plot_data,plot_file_path)

                    # Plot Score file
                    print(f"\t- Plot Score data")
                    plot_score_data = fetch_score_data(dataset_parameters)
                    score_file_path = f'{dataset_file_path_prefix}_plot_score.json'
                    write_data(plot_score_data,score_file_path)

                    # # Add/update entry in omicspred_plot
                    # if dataset_name and dataset_name != '':
                    #     dataset_name = dataset_name.replace('_',' ')
                    # try:
                    #     filters = [Q(platform_name=platform_name),Q(pmid=pmid)]
                    #     if dataset_name and dataset_name != '':
                    #         filters.append(Q(dataset_name=dataset_name))
                    #     plot = Plot.objects.using('plot').get(reduce(operator.and_,filters))
                    #     plot.score_data=plot_score_data
                    #     plot.save(using='plot')
                    # except Plot.DoesNotExist:
                    #     plot = Plot(pmid=pmid, platform_name=platform_name, score_data=plot_score_data)
                    #     if dataset_name and dataset_name != '':
                    #         plot.dataset_name = dataset_name
                    #     plot.save(using='plot')
            else:
                # Plot file
                print(f"\t- Plot data")
                plot_data = fetch_plot_data(parameters)
                plot_file_path = f'{file_path_prefix}_plot.json'
                write_data(plot_data,plot_file_path)

                # Plot Score file
                print(f"\t- Plot Score data")
                plot_score_data = fetch_score_data(parameters)
                score_file_path = f'{file_path_prefix}_plot_score.json'
                write_data(plot_score_data,score_file_path)