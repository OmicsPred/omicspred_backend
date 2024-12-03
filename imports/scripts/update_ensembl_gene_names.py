from omicspred.models import Gene, Transcript

input_file = '/Users/lg10/Workspace/datafiles/OmicsPred/Homo_sapiens.GRCh38.110.gtf'
# input_file = '/Users/lg10/Workspace/datafiles/OmicsPred/Homo_sapiens.GRCh38.110_sample.gtf'

ens2hgnc = {}
gene_biotypes_data = {}
transcript_biotypes_data = {}

ensg_stable_ids = []
enst_stable_ids = []

gene_id = 'gene_id'
gene_name = 'gene_name'
gene_biotype = 'gene_biotype'
trans_id = 'transcript_id'
trans_name = 'transcript_name'
trans_biotype ='transcript_biotype'

labels = [gene_id,gene_name,gene_biotype,trans_id,trans_name,trans_biotype]


def collect_data():
    # Collect gene information from the data file and store it in dictionaries
    print("- Collect data ...")
    with open(input_file) as f:
        for line in f:
            if line.startswith('#'):
                continue

            data = line.split('\t')

            # Annotations
            ens_data = {}
            annotations = data[8]
            annotations_list = annotations.replace('"','').split('; ')
            for annotation in annotations_list:
                key,value = annotation.split(' ',1)
                # print(f'{key}: {value}')
                for label in labels:
                    if key == label:
                        ens_data[label] = value
            ens_keys = ens_data.keys()

            # Gene data
            if gene_id in ens_keys:
                # Gene stable ID
                ensg = ens_data[gene_id]
                # Gene name
                if gene_name in ens_keys:
                    ens2hgnc[ensg] = ens_data[gene_name]

                # Gene biotype
                if gene_biotype in ens_keys:
                    # print(f"- {ensg}: {ens_data[gene_biotype]}")
                    gene_biotypes_data[ensg] = ens_data[gene_biotype]

            # Transcript data
            if trans_name in ens_keys:
                enst = ens_data[trans_id]
                # Transcript biotype
                if trans_biotype in ens_keys:
                    transcript_biotypes_data[enst] = ens_data[trans_biotype]


def update_genes():
    print("- Update gene names ...")
    ensg_stable_ids = ens2hgnc.keys()
    ensg_bt_ids = gene_biotypes_data.keys()

    counts = { 'names_diff': 0, 'syn': 0}
    # Update Genes: ENSG, HGNC and Biotype
    op_genes = Gene.objects.all()
    for op_gene in op_genes:
        gene_id = op_gene.external_id
        op_gene_name = op_gene.name
        flag_updated = False
        if gene_id and op_gene_name:
            if gene_id in ensg_stable_ids:
                ens_gene_name = ens2hgnc[gene_id]
                if ens_gene_name != op_gene_name:
                    if not '.' in op_gene_name:
                        op_gene.synonyms = [{"name": ens_gene_name}]
                        print(f"{gene_id}: OP {op_gene_name} is now synonym of HGNC {ens_gene_name}")
                        counts['syn'] += 1
                    else:
                        print(f"{gene_id}: HGNC {ens_gene_name} different from OP {op_gene_name}")
                    op_gene.name = ens_gene_name
                    flag_updated = True
                    counts['names_diff'] += 1
        # Gene biotype
        if gene_id in ensg_bt_ids:
            # print(f"- {gene_id}: {gene_biotypes_data[gene_id]}")
            op_gene.biotype = gene_biotypes_data[gene_id]
            flag_updated = True
        if flag_updated:
            op_gene.save()
    return counts


def update_transcripts():
    print("- Update transcript biotypes ...")
    enst_bt_ids = transcript_biotypes_data.keys()

    op_transcripts = Transcript.objects.all()
    for op_transcript in op_transcripts:
        trans_id = op_transcript.external_id
        # Transcript biotype
        if trans_id in enst_bt_ids:
            op_transcript.biotype = transcript_biotypes_data[trans_id]
            op_transcript.save()


###############################################################

def run():
    collect_data()
    count_diffs = update_genes()
    update_transcripts()

    print(f'COUNT GENES FROM FILE: {len(ensg_stable_ids)}')
    # print(f'COUNT HGNCs FROM FILE: {len(ensg_hgncs)}')
    print('--------------------------------------')
    print(f'COUNT Gene names that differ: {count_diffs["names_diff"]}')
    print(f'COUNT Gene synonyms: {count_diffs["syn"]}')
    # print(f'COUNT HGNC ID retrieved: {count_ensg_id_retrieved}')
    # print(f'COUNT ENSG ID retrieved: {count_hgnc_id_retrieved}')
