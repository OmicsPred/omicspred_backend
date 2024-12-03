import os
import xml.etree.ElementTree as ET
from omicspred.models import Protein

# Download files from UniProt FTP (uniprot_trembl_human.xml.gz and uniprot_sprot_human.xml.gz)
# and use uncompressed version: 
# https://ftp.ebi.ac.uk/pub/databases/uniprot/current_release/knowledgebase/taxonomic_divisions/
uniprot_files = ['uniprot_trembl_human.xml','uniprot_sprot_human.xml']
ixid_uri = "http://uniprot.org/uniprot"


## ===== Version using the UniProt REST API (not suitable to run for thousand of entries) ===== ##
# url_root = "https://www.ebi.ac.uk/proteins/api/proteins/"
# def rest_api(uniprot_id):
#     response = requests.get(f"{url_root}{uniprot_id}", headers={ "Accept" : "application/json"})
#     if not response.ok:
#         response.raise_for_status()
#         sys.exit()
#     return response.json()

# def get_synonyms_from_rest_api(uniprot_id):
#     synonyms = []
#     result = rest_api(uniprot_id)
#     if 'protein' in result.keys():
#         if 'alternativeName' in result['protein'].keys():
#             for alt_protein in result['protein']['alternativeName']:
#                 pr_name = ''
#                 if 'fullName' in alt_protein.keys():
#                     pr_name = alt_protein['fullName']['value']
#                 if 'shortName' in alt_protein.keys():
#                     short_names_list = []
#                     for short_name in alt_protein['shortName']:
#                         short_name_value = short_name['value']
#                         short_names_list.append(short_name_value)
#                     short_names = ', '.join(short_names_list)
#                     pr_name += f" [{short_names}]" if pr_name != '' else short_names
#                 if pr_name != '':
#                     synonyms.append(pr_name)
#     return [{'name':x} for x in synonyms]                


def get_node_tag_name(node_tag:str) -> str:
    return '{'+ixid_uri+'}'+node_tag

def parse_uniprot_files(uniprot_dir):
    synonyms = {}
    count_total_entries = 0
    for uniprot_file in uniprot_files:
        print(f"# Parse UniProt file {uniprot_file}")
        # root = ET.parse(f'{uniprot_dir}{uniprot_file}')
        print(f'  > Start browsing the document')
        count_file_entries = 0
        # for entry in root.iter():
        # for (event, elem) in ET.iterparse(f'{uniprot_dir}{uniprot_file}',['start','end']):
        for (event, elem) in ET.iterparse(f'{uniprot_dir}{uniprot_file}'):
            if event == 'end':
                if elem.tag == get_node_tag_name('entry'):
                    count_file_entries += 1
                    count_total_entries += 1
                    if str(count_file_entries).endswith('0000'):
                        print(f'  - {count_file_entries} entries')
                    accession = elem.findtext(get_node_tag_name('accession'))
                    protein = elem.find(get_node_tag_name('protein'))
                    alternative_names = protein.findall(get_node_tag_name('alternativeName'))
                    for alternative_name in alternative_names:
                        alt_pr_name = ''
                        # Alternative name
                        full_name_tag = alternative_name.find(get_node_tag_name('fullName'))
                        if full_name_tag != None:
                            alt_pr_name += full_name_tag.text
                        # Alternative short name 
                        short_name_tags = alternative_name.findall(get_node_tag_name('shortName'))
                        if short_name_tags:
                            short_names_list = [x.text for x in short_name_tags]
                            short_names = ', '.join(short_names_list)
                            alt_pr_name += f" [{short_names}]" if alt_pr_name != '' else short_names
                        
                        if alt_pr_name != '':
                            if accession not in synonyms.keys():
                                synonyms[accession] = []
                            synonyms[accession].append(alt_pr_name)
                    elem.clear()
    print(f"Total UniProt entries: {count_total_entries}")
    return synonyms


# Command line:
# python manage.py runscript update_uniprot_synonyms --script-args <path_to_data_directory>
def run(*args):

    uniprot_dir = None

    if args:
        uniprot_dir = args[0]
        if not uniprot_dir.endswith('/'):
            uniprot_dir += '/'
        # Check directory
        if not os.path.isdir(uniprot_dir):
            print("Directory '"+uniprot_dir+"' can't be found")
            exit(1)
    else:
        print('''Please, provides an UniProt directory as parameter. e.g.:\n\tpython manage.py runscript update_uniprot_synonyms --script-args <path_to_data_directory>''')
        exit(1)
    

    synonyms = parse_uniprot_files(uniprot_dir)
    synonyms_keys = synonyms.keys()
    proteins = Protein.objects.all()

    count_synonym_found = 0
    print(f"# Assign synonyms")
    for protein in proteins:
        if protein.external_id:
            if protein.external_id in synonyms_keys:
                count_synonym_found += 1
                syn = [{'name': x} for x in synonyms[protein.external_id]]
                if syn:
                    protein.synonyms = syn
                    protein.save()
                else:
                    print(f"  - {protein.external_id}: EMPTY synonyms entry")
            else:
                print(f"  - {protein.external_id}: NO synonyms")
        else:
            print(f"  ! No external ID for protein {protein.id}")

    print("\n------------------------------------")
    print(f"Total OP proteins: {len(proteins)}")
    print(f"Total UniProt entries with syn: {len(synonyms_keys)}")
    print(f"Total syn found: {count_synonym_found}")
