import requests
import time
import json

# platforms = {
#     'Nightingale': 'metabolomics',
#     'Metabolon': 'metabolomics',
#     'Olink': 'proteomics',
#     'Somalogic': 'proteomics',
#     'Illumina RNAseq': 'transcriptomics'
# }

platforms = {
    'Somalogic': 35202437,
}


url_root = 'http://127.0.0.1:7000/rest'
plot_url_root = f'{url_root}/plot/search?format=json&platform='
plot_score_url_root = f'{url_root}/plot/score/search?format=json&platform='
table_url_root = f'{url_root}/'

default_path = '/Users/lg10/Workspace/git/fork/omicspred_frontend/public/data'


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


def run():

    for platform in platforms.keys():
        print(f"# {platform}:")
        platform_name = platform.replace(' ','_')
        pmid = platforms[platform]
        parameters = f'{platform}&pmid={pmid}'

        # Plot file
        print(f"\t- Plot data")
        plot_data = rest_api_call(plot_url_root, parameters)
        with open(f'{default_path}/{platform_name}_{pmid}_plot.json', mode="w") as f:
            # f.write(json.dumps(plot_data, indent=4))
            f.write(json.dumps(plot_data))

        # Plot Score file
        print(f"\t- Plot Score data")
        plot_score_data = rest_api_call(plot_score_url_root, parameters)
        with open(f'{default_path}/{platform_name}_{pmid}_plot_score.json', mode="w") as f:
            # f.write(json.dumps(plot_score_data, indent=4))
            f.write(json.dumps(plot_score_data))

        # # Table file
        # print(f"\t- Table data")
        # table_data = rest_api_call(table_url_root+platforms[platform]+'/', platform)
        # with open(f'{default_path}/{platform_name}_table.json', mode="w") as f:
        #     # f.write(json.dumps(table_data, indent=4))
        #     f.write(json.dumps(table_data))
