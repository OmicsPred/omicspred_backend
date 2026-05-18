import requests
from omicspred.models import Phenotype


categories_info = {
    'autoimmune disease': 'Immune system disorder',
    'biological process': 'Biological process',
    'biological_process': 'Biological process',
    'body weights and measures': 'Body measurement',
    'cancer': 'Cancer',
    'cardiovascular disease': 'Cardiovascular disease',
    'cardiovascular disorder': 'Cardiovascular disease',
    'cardiovascular measurement': 'Cardiovascular measurement',
    'digestive system disease': 'Digestive system disorder',
    'digestive system disorder': 'Digestive system disorder',
    'disease': 'Other disease',
    'drug dependence': 'Neurological disorder',
    'experimental factor': 'Other trait',
    'hematological measurement': 'Hematological measurement',
    'hereditary neurological disease': 'Neurological disorder',
    'inflammatory disease': 'Immune system disorder',
    'immune system disease': 'Immune system disorder',
    'immune system disorder': 'Immune system disorder',
    'inflammatory biomarker measurement': 'Inflammatory measurement',
    'lipid or lipoprotein measurement': 'Lipid or lipoprotein measurement',
    'liver enzyme measurement': 'Liver enzyme measurement',
    'measurement': 'Other measurement',
    'metabolic disease': 'Metabolic disorder',
    'metabolic disorder': 'Metabolic disorder',
    'mouth disorder': 'Digestive system disorder',
    'neoplasm': 'Cancer',
    'nervous system disease': 'Neurological disorder',
    'nervous system disorder': 'Neurological disorder',
    'psychiatric disorder': 'Neurological disorder',
    'response to drug': 'Response to drug'
}

category_label_priority = ['Cancer', 'Cardiovascular disease', 'Neurological disorder', 'Immune system disorder', 'Metabolic disorder']

exclude_terms = [
    'biological process',
    # 'biological sex',
    'disease',
    # 'disease by anatomical system',
    # 'disease by cellular process disrupted',
    # 'disease by subcellular system affected',
    # 'disease characteristic',
    # 'disorder by anatomical region',
    # 'disposition',
    'experimental factor',
    # 'information entity',
    # 'material property',
    'measurement',
    # 'phenotypic sex',
    # 'process',
    # 'quality',
    # 'Thing'
]


def ols_rest_call(trait_id:str,trait_label:str):
    filtered_ancestors = []
    # Case where the trait is one of the retained ancestor
    if trait_label in categories_info.keys():
        filtered_ancestors.append(trait_label)
        return filtered_ancestors

    obo_id = trait_id.replace('_',':')
    rest_url = f'https://www.ebi.ac.uk/ols4/api/ontologies/efo/ancestors?id={obo_id}'
    response = requests.get(rest_url, headers={ "Content-Type" : "application/json"})
    response_json = response.json()
    ancestors = set()
    if response_json:
        if '_embedded' in response_json.keys():
            response = response_json['_embedded']['terms']
            for term in response:
                label = term['label']
                if label in categories_info.keys():
                    ancestors.add(label)
    # Filter ancestors
    for ancestor in ancestors:
        if ancestor not in exclude_terms:
            filtered_ancestors.append(ancestor)
    if filtered_ancestors:
        return filtered_ancestors
    else:
        for ancestor in ancestors:
            if ancestor == 'experimental factor' and ('disease' in ancestors or 'biological process' in ancestors or 'biological_process' in ancestors or 'measurement' in ancestors):
                continue
            else:
                filtered_ancestors.append(ancestor)
    return filtered_ancestors


def run():
    phenotypes = Phenotype.objects.filter(category='')
    print(f"Phenotypes: {len(phenotypes)}")
    count_phe = 0
    for phenotype in phenotypes:
        print(f"> Phenotype {phenotype.id} ({phenotype.label})")
        count_phe += 1
        if str(count_phe).endswith('00'):
            print(f'  - {count_phe} done')
        id = phenotype.id
        # cat = phenotype.category
        ancestors = ols_rest_call(id, phenotype.label)
        print(f">> ANCESTORS: {ancestors}")
        categories_occurences = {}
        # Occurences
        for category in ancestors:
            category_label = categories_info[category]
            if category_label not in categories_occurences.keys():
                categories_occurences[category_label] = 0
            categories_occurences[category_label] += 1
        categories_list = categories_occurences.keys()
        categories = list(categories_occurences.keys())
        # Most occurent
        for category in categories_list:
            if categories_occurences[category] > 1:
                categories = [category]
                break
        # Category priority
        if len(categories) > 1:
            for category in category_label_priority:
                if category in categories:
                    categories = [category]
                    break
        categories_string = '| '.join(categories)
        phenotype.category = categories_string
        phenotype.save()