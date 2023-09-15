import requests
from omicspred.models import Gene, Transcript

input_file = '/Users/lg10/Workspace/datafiles/OmicsPred/Homo_sapiens.GRCh38.110.gtf'
# input_file = '/Users/lg10/Workspace/datafiles/OmicsPred/Homo_sapiens.GRCh38.110_sample.gtf'

ens2hgnc = {}
hgnc2ens = {}
transcripts = {}

count_ensg_id_retrieved = 0
count_hgnc_id_retrieved = 0

gene_id = 'gene_id'
gene_name = 'gene_name'
trans_id = 'transcript_id'
trans_name = 'transcript_name'

gene_chr = {}

labels = [gene_id,gene_name,trans_id,trans_name]

def ens_rest_call(gene_name):
    stable_id = None
    rest_url = f'https://rest.ensembl.org/xrefs/symbol/homo_sapiens/{gene_name}'
    response = requests.get(rest_url, headers={ "Content-Type" : "application/json"})
    response_json = response.json()
    if response_json:
        count_ens = 0
        ensg = None
        for resp in response_json:
            if resp['id'].startswith('ENSG'):
                count_ens += 1
                ensg = resp['id']
        if ensg and count_ens == 1:
            stable_id = ensg
            print(f"]] {gene_name}: Stable ID found => {stable_id}")
        elif count_ens > 1:
            print(f"]] {gene_name}: Too many stable IDs found ({count_ens})")
        elif ensg == None:
            print(f"]] {gene_name}: no Ensembl stable IDs found")
    else:
        print(f"]] {gene_name}: no found")
    return stable_id


def collect_data():
    # Collect gene information from the data file and store it in dictionaries
    with open(input_file) as f:
        for line in f:
            if line.startswith('#'):
                continue

            data = line.split('\t')
            chr = data[0]
            annotations = data[8]
            annotations = annotations.replace('"','')
            if gene_name in annotations:
                # print(annotations)
                annotations_list = annotations.split('; ')

                ens_data = {}
                for annotation in annotations_list:
                    key,value = annotation.split(' ',1)
                    # print(f'{key}: {value}')
                    for label in labels:
                        if key == label:
                            ens_data[label] = value
                ens_keys = ens_data.keys()
                # Genes
                if all(x in ens_keys for x in [gene_id,gene_name]):
                    ensg = ens_data[gene_id]
                    hgnc = ens_data[gene_name]

                    ens2hgnc[ensg] = hgnc
                    if not hgnc in hgnc2ens.keys():
                        hgnc2ens[hgnc] = set()
                    hgnc2ens[hgnc].add(ensg)
                    gene_chr[ensg] = chr

                    # Transcripts
                    if all(x in ens_keys for x in [trans_id,trans_name]):
                        enst = ens_data[trans_id]
                        trans = ens_data[trans_name]
                        transcripts[enst] = { 'name': trans, 'gene': ensg}


def update_genes():
    ensg_stable_ids = ens2hgnc.keys()
    ensg_hgncs = hgnc2ens.keys()

    # Update Genes: ENSG and HGNC
    op_genes = Gene.objects.all()
    for op_gene in op_genes:
        if op_gene.external_id and not op_gene.name:
            if op_gene.external_id in ensg_stable_ids:
                # print(f'- Found missing HGNC for {op_gene.external_id}: {ens2hgnc[op_gene.external_id]}')
                op_gene.name = ens2hgnc[op_gene.external_id]
                op_gene.save()
                count_ensg_id_retrieved += 1
        elif op_gene.name and not op_gene.external_id:
            if op_gene.name in ensg_hgncs:
                # print(f'- Found missing ENSG ID for {op_gene.name}: {hgnc2ens[op_gene.name]}')
                found_ensg = list(hgnc2ens[op_gene.name])
                gene_stable_id = found_ensg[0]
                if len(found_ensg) > 1:
                    print(f'- Found several ENSG IDs for {op_gene.name}: {found_ensg}')
                    map_y = None
                    map_x = None
                    for ensg in found_ensg:
                        if gene_chr[ensg] == 'X':
                            map_x = ensg
                        elif gene_chr[ensg] == 'Y':
                            map_y = ensg
                    if map_y and map_x:
                        print(f'  => Selected: {map_x}')
                        gene_stable_id = map_x
                op_gene.external_id = gene_stable_id
                op_gene.external_id_source = 'Ensembl'
                op_gene.save()
                count_hgnc_id_retrieved += 1
            else:
                gene_stable_id = ens_rest_call(op_gene.name)
                if gene_stable_id:
                    op_gene.external_id = gene_stable_id
                    op_gene.external_id_source = 'Ensembl'
                    op_gene.save()


def add_transcripts():
    # Create Transcript entries with Gene link
    new_op_genes = Gene.objects.all()
    gene_data = {x.external_id:x for x in Gene.objects.filter(external_id__isnull=False)}
    gene_ids_list = gene_data.keys()

    count_tr = len(transcripts.keys())
    count_tr_gene = 0
    for tr_id in transcripts.keys():
        try:
            tr_obj = Transcript.objects.get(external_id=tr_id)
        except Transcript.DoesNotExist:
            tr_name = transcripts[tr_id]['name']
            tr_gene_id = transcripts[tr_id]['gene']
            if tr_gene_id in gene_ids_list:
                gene = gene_data[tr_gene_id]
                op_trans = Transcript(
                    name=tr_name,
                    external_id=tr_id,
                    external_id_source='Ensembl',
                    gene=gene
                )
                op_trans.save()
                count_tr_gene += 1
    print(f'count_tr: {count_tr}')
    print(f'count_tr_gene: {count_tr_gene}')


###############################################################

def run():
    collect_data()
    update_genes()
    add_transcripts()

    print(f'COUNT GENES FROM FILE: {len(ensg_stable_ids)}')
    print(f'COUNT HGNCs FROM FILE: {len(ensg_hgncs)}')
    print('--------------------------------------')
    print(f'COUNT HGNC ID retrieved: {count_ensg_id_retrieved}')
    print(f'COUNT ENSG ID retrieved: {count_hgnc_id_retrieved}')
