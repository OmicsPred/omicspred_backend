import pandas as pd
from imports.omicspred.parsers.data_content import *
from omicspred.models import Score,SourceAnnotations


annotation_headers = {
    'Ensembl ID': 'gene_id',
    'Gene': 'gene_name',
    'UniProt ID': 'protein_id',
    'Protein': 'protein_name',
    'Biomarker Name': 'metabolite_name',
    'Biochemical Name': 'metabolite_name',
    'Metabolon ID': 'metabolite_id'
}
annotation_headers_list = annotation_headers.keys()

def fetch_annotations(filepath):
    count_annotations = 0
    df = pd.read_csv(filepath)
    df = df.fillna('') # Replace NaN values by ''
    for index, row in df.iterrows():
        annotations = {}
        cols = row.keys()
        score_id = row['OMICSPRED ID']
        for col_name in annotation_headers_list:
            if col_name in cols:
                value = row[col_name]
                # Skip empty values
                if value and value not in ['']:
                    annotation_key = annotation_headers[col_name]
                    annotations[annotation_key] = value
        if score_id and annotations:
            try:
                score = Score.objects.get(id=score_id)
                sa_model = SourceAnnotations(score=score,annotations=annotations)
                sa_model.save()
                count_annotations += 1
            except Score.DoesNotExist:
                print(f"Can't find a score object with the ID: {score_id}")
    print(f">> Annotations: {count_annotations}/{len(df.index)}")

def run():
    path = '/Users/lg10/Workspace/git/clone/OmicsPred_bak/src/data'

    for study in studies.keys():
        print(f'\n\n##### {study} #####')
        filename = study.split('_')[-1]
        filepath = f'{path}/paper_data/{filename}.csv'
        source_annotations = fetch_annotations(filepath)
