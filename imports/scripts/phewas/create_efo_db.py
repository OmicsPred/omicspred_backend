import os
import sqlite3
import json
import requests
from imports.config import phewas_dir, efo_sqlite_filepath


# https://github.com/EBISPOT/efo/releases/download/v3.88.0/efo.json
# https://github.com/EBISPOT/efo/releases/
efo_file = 'efo.json'
efo_filepath = f'{phewas_dir}/metadata/{efo_file}'

def create_table():
    # Remove existing database (cleaner)
    if efo_sqlite_filepath.endswith('.db'):
        os.remove(efo_sqlite_filepath)
        # Create database
        sqlite_create_table = """
            CREATE TABLE IF NOT EXISTS efo (
                id TEXT,
                label TEXT,
                alt_label TEXT,
                description TEXT,
                url TEXT,
                replacement_id TEXT,
                PRIMARY KEY(id)
            );
            """
        con = sqlite3.connect(efo_sqlite_filepath)
        cur = con.cursor()
        cur.execute(sqlite_create_table)
        con.commit()
        cur.close()
        con.close()
    else:
        print(f"- Wrong SQLite file extension for {efo_sqlite_filepath}")
        exit(0)


def insert_phenotype(efo_data:tuple):
    con = sqlite3.connect(efo_sqlite_filepath)
    cur = con.cursor()
    cur.execute('INSERT INTO efo (id,label,alt_label,description,url,replacement_id) VALUES (?, ?, ?, ?, ?, ?)', efo_data)
    con.commit()
    cur.close()
    con.close()


def get_new_id(properties:list):
    for property in properties:
        if property["pred"] == "http://purl.obolibrary.org/obo/IAO_0100001":
            url = property["val"]
            new_id = url.rsplit('/', 1)[-1]
            return new_id
    return None


def ols_rest_call(trait_id:str):
    obo_id = trait_id.replace('_',':')
    rest_url = f'https://www.ebi.ac.uk/ols4/api/ontologies/efo/terms?obo_id={obo_id}'
    response = requests.get(rest_url, headers={ "Content-Type" : "application/json"})
    response_json = response.json()
    if response_json:
        if '_embedded' in response_json.keys():
            response = response_json['_embedded']['terms']
            if len(response) == 1:
                response = response[0]

                if response['is_obsolete']:
                    if 'term_replaced_by' in response.keys():
                        new_term_uri = response['term_replaced_by']
                        if not new_term_uri:
                            print(f">>> {trait_id}: missing 'term_replaced_by' -> {new_term_uri}")
                        else:
                            new_term_id = new_term_uri.rsplit('/', 1)[-1]
                            return new_term_id     
    return None


def run():
    efo_ids = set()
    count_efos = 0
    count_entries = 0
    create_table()
    with open(efo_filepath) as f:
        data = json.load(f)

        for entry in data['graphs'][0]['nodes']:
            count_entries += 1
            if str(count_efos).endswith('0000'):
                print(f'- {count_efos} done')
            if 'lbl' in entry.keys():
                label = entry['lbl']
                url = entry['id']
                id = url.rsplit('/', 1)[-1]
                alt_label = None
                new_id = None
                if label.startswith('obsolete_'):
                    alt_label = label.replace('obsolete_', '')
                    if 'basicPropertyValues' in entry['meta'].keys():
                        new_id = get_new_id(entry['meta']['basicPropertyValues'])
                    else:
                        print(f"  - Try fetch new ID for {id}")
                        new_id = ols_rest_call(id)
                    # url = new_data[1]
                description = None
                if 'meta' in entry.keys():
                    if 'definition' in entry['meta'].keys():
                        if 'val' in entry['meta']['definition'].keys():
                            description = entry['meta']['definition']['val']
                if id not in efo_ids:
                    efo_ids.add(id)
                    efo_data = (id,label,alt_label,description,url,new_id)
                    insert_phenotype(efo_data)
                    count_efos += 1
    print(f"Total entries inserted: {count_efos}")
    print(f"Total entries: {count_entries}")


