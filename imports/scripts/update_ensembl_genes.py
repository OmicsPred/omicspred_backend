import requests
import csv
from omicspred.models import Gene, Transcript


workdir = '/Users/lg10/Workspace/datafiles/OmicsPred'
# GTF file: https://ftp.ensembl.org/pub/current_gtf/homo_sapiens/
input_file = f'{workdir}/Homo_sapiens.GRCh38.113.gtf'
# BioMart export (attributes 'Gene stable ID', 'Gene description' | no chromosome filtering)
ensg_description_file = f'{workdir}/ensg_description.txt'

ens2hgnc = {}
hgnc2ens = {}
transcripts = {}
ens_biotype = {}

gene_id = 'gene_id'
gene_name = 'gene_name'
gene_biotype = 'gene_biotype'
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
            print(f"  ]] {gene_name}: Stable ID found => {stable_id}")
        elif count_ens > 1:
            print(f"  ]] {gene_name}: Too many stable IDs found ({count_ens})")
        elif ensg == None:
            print(f"  ]] {gene_name}: no Ensembl stable IDs found")
    else:
        print(f"  ]] {gene_name}: no found")
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
                biotype = None
                for annotation in annotations_list:
                    key,value = annotation.split(' ',1)
                    # print(f'{key}: {value}')
                    for label in labels:
                        if key == label:
                            ens_data[label] = value
                        if key == gene_biotype:
                            biotype = value
                if gene_id in ens_data.keys():
                    ensg_id = ens_data[gene_id]
                    ens_biotype[ensg_id] = biotype

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


def update_genes(ensg_stable_ids,ensg_hgncs,count_ensg_id_retrieved,count_hgnc_id_retrieved):
    # ensg_stable_ids = ens2hgnc.keys()
    # ensg_hgncs = hgnc2ens.keys()
    # Update Genes: ENSG and HGNC
    print("- Update gene names, external IDs and biotypes")
    biotypes = ens_biotype.keys()
    op_genes = Gene.objects.all()
    for op_gene in op_genes:
        is_updated = False
        if op_gene.external_id:
            if op_gene.external_id in ensg_stable_ids:
                if not op_gene.name:
                    # print(f'- Found missing HGNC for {op_gene.external_id}: {ens2hgnc[op_gene.external_id]}')
                    op_gene.name = ens2hgnc[op_gene.external_id]
                    count_ensg_id_retrieved += 1
                    is_updated = True
            else:
                op_gene.retired_gene_model = True
                is_updated = True
        elif op_gene.name:
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
                count_hgnc_id_retrieved += 1
                is_updated = True
            else:
                gene_stable_id = ens_rest_call(op_gene.name)
                if gene_stable_id:
                    op_gene.external_id = gene_stable_id
                    op_gene.external_id_source = 'Ensembl'
                    is_updated = True
        # Add gene biotype
        if op_gene.external_id and not op_gene.biotype:
            if op_gene.external_id in biotypes:
                op_gene.biotype = ens_biotype[op_gene.external_id]
                is_updated = True

        if is_updated == True:
            op_gene.save()


def add_transcripts():
    # Create Transcript entries with Gene link
    print("- Add transcripts")
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
    print(f'  > count_tr: {count_tr}')
    print(f'  > count_tr_gene: {count_tr_gene}')


def update_description():
    gene_data = {}
    print("- Update gene descriptions")
    print("  > Read data file")
    with open(ensg_description_file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        next(reader, None)  # skip the headers
        for row in reader:
            ensg_id = row[0]
            desc = row[1].split(' [Source')[0]
            gene_data[ensg_id] = desc

    genes = Gene.objects.filter(description__isnull=True)
    print(f"  > Update {len(genes)} genes")
    data_ids_list = gene_data.keys()
    for gene in genes:
        ensg_id = gene.external_id
        if ensg_id:
            if ensg_id in data_ids_list:
                gene.description = gene_data[ensg_id]
                gene.save()


###############################################################

def run():
    count_ensg_id_retrieved = 0
    count_hgnc_id_retrieved = 0

    collect_data()

    ensg_stable_ids = ens2hgnc.keys()
    ensg_hgncs = hgnc2ens.keys()

    update_genes(ensg_stable_ids,ensg_hgncs,count_ensg_id_retrieved,count_hgnc_id_retrieved)
    add_transcripts()

    update_description()

    print(f'COUNT GENES FROM FILE: {len(ensg_stable_ids)}')
    print(f'COUNT HGNCs FROM FILE: {len(ensg_hgncs)}')
    print('--------------------------------------')
    print(f'COUNT HGNC ID retrieved: {count_ensg_id_retrieved}')
    print(f'COUNT ENSG ID retrieved: {count_hgnc_id_retrieved}')
