import re
from omicspred.models import Gene, Protein

# https://ftp.ensembl.org/pub/current_tsv/homo_sapiens/
# input_file = '/Users/lg10/Workspace/datafiles/OmicsPred/Homo_sapiens.GRCh38.113.uniprot.tsv'
input_file = '/Users/lg10/Workspace/datafiles/OmicsPred/Homo_sapiens.GRCh38.115.uniprot.tsv'
genes = {}
proteins = {}

def update_proteins():
    op_proteins = Protein.objects.all()
    op_genes_list = [ x.external_id for x in Gene.objects.all()]

    # Update proteins from DB, using collected information from the data file
    count_op_pr = op_proteins.count()
    count_pr_gene = 0
    pr_ens_list = genes.keys()
    count_pr = 0
    count_missing_gene = 0
    for pr_obj in op_proteins:
        count_pr += 1
        if re.search('00$',str(count_pr)):
            print(f"- {count_pr}/{len(op_proteins)}")
        if pr_obj.external_id in pr_ens_list:
            ens_genes = genes[pr_obj.external_id]
            gene_found = False
            # Select Gene in genes mapped list (same gene symbols on chr, scaffold and haplotypes)
            for ens_gene in ens_genes:
                if ens_gene in op_genes_list:
                    try:
                        gene_obj = Gene.objects.get(external_id=ens_gene)
                        # print(f"V - {pr_obj.external_id}: gene '{ens_gene}' found!")
                        pr_obj.gene = gene_obj
                        pr_obj.save()
                        count_pr_gene += 1
                        gene_found = True
                        break
                    except:
                        print(f"  -> {ens_gene}: more than 1 gene found")
                        exit(0)
                # else:
                #     count_missing_gene += 1
            if not gene_found:
                count_missing_gene += 1
                # print(f"  !! {pr_obj.external_id}: gene '{ens_gene}' NOT found!")
    print(f'>> Updated proteins: {count_pr_gene}/{count_op_pr}')
    print(f'>> Missing genes: {count_missing_gene}')


###############################################################

def run():
    # Collect protein and gene information from the data file and store it in dictionaries
    with open(input_file) as f:
        for line in f:
            if line.startswith('ENSG'):
                data = line.split('\t')
                gene    = data[0]
                uniprot = data[3]
                if uniprot not in genes.keys():
                    genes[uniprot] = set()
                genes[uniprot].add(gene)
    update_proteins()
