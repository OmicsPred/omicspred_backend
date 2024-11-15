import os
import subprocess
import requests

url_root = 'https://reactome.org/download/current/'
default_reactome_dir = '/Users/lg10/Workspace/datafiles/OmicsPred/Reactome'


def download_file(url:str,file_name:str,path:str,human_file_name:str=None) -> bool:
    download_success = False
    if not path.endswith('/'):
        path += '/'
    file_target = f"{path}{file_name}"
    try:
        response = requests.get(url, stream=True)
        with open(file_target, mode="w") as file:
            for chunk in response.iter_content(chunk_size=10 * 1024):
                file.write(chunk.decode("utf-8"))

        if os.path.isfile(file_target) and os.path.getsize(file_target) > 0:
            print("  - File downloaded")
            if human_file_name:
                try:
                    file_human = f"{path}{human_file_name}"
                    human_data = subprocess.run([f"grep 'Homo sapiens' {file_target}"], shell=True, capture_output=True, text=True)
                    with open(file_human, mode="w") as file_new:
                        file_new.write(human_data.stdout)
                    if os.path.isfile(file_human) and os.path.getsize(file_human) > 0:
                        print("  - Human data extracted")
                        download_success = True
                        # Remove original file
                        try:
                            os.remove(file_target)
                        except Exception as e:
                            print(f"  > ERROR - can't remove the file {file_target}: {e}")
                except Exception as e:
                    print(f"  > ERROR with the Human data extraction: {e}")
            else:
                download_success = True
        else:
            print("  > ERROR - file_target does not exist or is empty")
                
    except Exception as e:
        print(f"  > ERROR with the file download: {e}")
    return download_success


# Command line:
# python manage.py runscript download_reactome_data --script-args <path_to_data_directory>
def run(*args):

    if args:
        reactome_dir = args[0]
    else:
        reactome_dir = default_reactome_dir

    # Check directory
    if not os.path.isdir(reactome_dir):
        print("Directory '"+reactome_dir+"' can't be found")
        exit(1)

    # Download ChEBI
    print("\n# Download ChEBI data")
    chebi_filename = 'ChEBI2Reactome.txt'
    chebi_download = download_file(f'{url_root}{chebi_filename}', chebi_filename, reactome_dir, 'ChEBI2Reactome_LOW_Levels_human.txt')
    if chebi_download:
        print(">> ChEBI data download done")
    else:
        print(">> ERROR with the ChEBI data download")

    # Download Ensembl
    print("\n# Download Ensembl data")
    ens_filename = 'Ensembl2Reactome.txt'
    ens_download = download_file(f'{url_root}{ens_filename}', ens_filename, reactome_dir, 'Ensembl2Reactome_LOW_Levels_human.txt')
    if ens_download:
        print(">> Ensembl data download done")
    else:
        print(">> ERROR with the Ensembl data download")

    # Download top level
    print("\n# Download Human Top Level data")
    top_level_file = 'human_top_level.json'
    top_level_download = download_file('https://reactome.org/ContentService/data/pathways/top/9606/', top_level_file, reactome_dir)
    if top_level_download:
        print(">> Top Level data download done")
    else:
        print(">> ERROR with the Top Level data download")


    # Download pathways hierarchy relationship
    print("\n# Download Reactome Pathways Relation data")
    pathways_filename = 'ReactomePathwaysRelation.txt'
    pathways_download = download_file(f'{url_root}{pathways_filename}', pathways_filename, reactome_dir)
    if pathways_download:
        print(">> Reactome Pathways Relation data download done")
    else:
        print(">> ERROR with the Reactome Pathways Relation data download")
