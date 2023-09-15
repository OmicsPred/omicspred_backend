from omicspred.models import Gene, Protein

input_file = '/Users/lg10/Workspace/datafiles/OmicsPred/Homo_sapiens.GRCh38.110.uniprot.tsv'

genes = {}
proteins = {}


def update_proteins():
    op_proteins = Protein.objects.all()
    op_genes_list = [ x.external_id for x in Gene.objects.all()]

    # Update proteins from DB, using collected information from the data file
    count_op_pr = op_proteins.count()
    count_pr_gene = 0
    pr_ens_list = genes.keys()
    for pr_obj in op_proteins:
        if pr_obj.external_id in pr_ens_list:
            ens_gene = genes[pr_obj.external_id]
            if ens_gene in op_genes_list:
                gene_obj = Gene.objects.get(external_id=ens_gene)
                # print(f"V - {pr_obj.external_id}: gene '{ens_gene}' found!")
                pr_obj.gene = gene_obj
                pr_obj.save()
                count_pr_gene += 1
            else:
                print(f"X - {pr_obj.external_id}: gene '{ens_gene}' NOT found!")
    print(f'>> Updated proteins: {count_pr_gene}/{count_op_pr}')


###############################################################

def run():
    # Collect protein and gene information from the data file and store it in dictionaries
    with open(input_file) as f:
        for line in f:
            if line.startswith('ENSG'):
                data = line.split('\t')
                gene    = data[0]
                uniprot = data[3]
                genes[uniprot] = gene
    update_proteins()
