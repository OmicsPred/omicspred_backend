import os, csv, json
from omicspred.models import Gene,Protein,Metabolite,Pathway,SuperPathway

default_reactome_dir = '/Users/lg10/Workspace/datafiles/OmicsPred/Reactome'

reactome_entities = {}
reactome_top_level = {}
reactome_top_level_synonyms = {}
reactome_low_to_top_level = {}
reactome_mapping_found = {}

pathway_source = 'Reactome'


def get_top_levels_list(reactome_top_level_file):
    top_level_file = open(reactome_top_level_file)
    top_level_data = json.load(top_level_file)
    for top_level in top_level_data:
        id = top_level["stId"]
        name = top_level["displayName"]
        synonyms = [ x for x in top_level["name"] if x != name]
        # print(f'{id}: {name}')
        reactome_top_level[id] = name
        if synonyms:
            reactome_top_level_synonyms[id] = synonyms
            # print(f'  > Syn: {synonyms}')
        try:
            superpathway = SuperPathway.objects.get(external_id=id)
        except SuperPathway.DoesNotExist:
            superpathway = SuperPathway(external_id=id,name=name,external_id_source=pathway_source)
            if synonyms:
                superpathway.synonyms = [{'name': x} for x in synonyms]
            superpathway.save()
    top_level_file.close()


def get_relations(reactome_relation_file):
     with open(reactome_relation_file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        tmp_relation = {}
        for row in reader:
            parent = row[0]
            child = row[1]
            if not parent.startswith('R-HSA-'):
                continue
            if child in tmp_relation.keys():
                tmp_relation[child].append(parent)
            else:
                tmp_relation[child] = [parent]
        for pathway in tmp_relation.keys():
            top_levels_list = fetch_top_level(tmp_relation,pathway,set())
            if top_levels_list:
                # top_level = [ reactome_top_level[x] for x in top_levels_list]
                # print(f'{pathway}: {" | ".join(top_level)}')
                reactome_low_to_top_level[pathway] = list(top_levels_list)


def fetch_top_level(relation_list,pathway,top_levels_list):
    for parent in relation_list[pathway]:
        if parent in reactome_top_level.keys():
            top_levels_list.add(parent)
            return top_levels_list
        else:
            top_levels_list = fetch_top_level(relation_list,parent,top_levels_list)
    return top_levels_list


def get_reactome_data(file):
    reactome_data = {}
    with open(file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        next(reader, None)  # skip the headers
        for row in reader:
            source_id = row[0]
            reactome_id = row[1]
            reactome_name = row[3]
            reactome_species = row[5]
            if reactome_species != 'Homo sapiens':
                continue

            reactome_info = { 
                'reactome_id': reactome_id,
                'reactome_name': reactome_name
            }
            if reactome_id not in reactome_entities.keys():
                reactome_entities[reactome_id] = reactome_name
            if source_id in reactome_data.keys():
                # print(f"> {source_id} has already a reactome association")
                reactome_data[source_id].append(reactome_info)
            else:
                reactome_data[source_id] = [reactome_info]
    return reactome_data


def import_reactome_entries():

    reactome_low_top_ids = reactome_low_to_top_level.keys()
    mapped_reactome_ids = reactome_mapping_found.keys()
    for entity_id in reactome_entities.keys():
        id = entity_id
        name = reactome_entities[entity_id]
        if id in mapped_reactome_ids:
            try:
                pathway = Pathway.objects.get(external_id=id)
                if id in reactome_low_top_ids:
                    current_superpathway_ids = [ x.external_id for x in pathway.superpathways.all()]
                    linked_superpathways = []
                    for superpathway_id in reactome_low_to_top_level[id]:
                        try:
                            superpathway = SuperPathway.objects.get(external_id=superpathway_id)
                            linked_superpathways.append(superpathway)
                        except SuperPathway.DoesNotExist:
                            print("/!\ Can't find the superpathway {superpathway_id} in the DB")
                    if linked_superpathways:
                        for superpathway in linked_superpathways:
                            if superpathway.external_id not in current_superpathway_ids:
                                pathway.superpathways.add(superpathway)
                        pathway.save()
            except Pathway.DoesNotExist:
                pathway = Pathway(external_id=id,name=name,external_id_source=pathway_source)
                pathway.save()
                if id in reactome_low_top_ids:
                    linked_superpathways = []
                    for superpathway_id in reactome_low_to_top_level[id]:
                        try:
                            superpathway = SuperPathway.objects.get(external_id=superpathway_id)
                            linked_superpathways.append(superpathway)
                        except SuperPathway.DoesNotExist:
                            print("/!\ Can't find the superpathway {superpathway_id} in the DB")
                    if linked_superpathways:
                        for superpathway in linked_superpathways:
                            pathway.superpathways.add(superpathway)
                        pathway.save()


def map_genes(reactome_ensembl_file):
    mappings = {}
    reactome_data = get_reactome_data(reactome_ensembl_file)

    reactome_ens_ids = reactome_data.keys()
    genes = Gene.objects.filter(external_id_source='Ensembl')
    count_omics = len(genes)
    count = 0
    for gene in genes:
        id = gene.external_id
        if id in reactome_ens_ids:
            reactome_entries = reactome_data[id]
            mappings[id] = reactome_entries
            for reactome_entry in reactome_entries:
                reactome_mapping_found[reactome_entry['reactome_id']] = True
            # print(f"- {gene.external_id}: {reactome_data[id]}")
            count += 1
    print(f"Ensembl-Reactome mappings: {count}/{count_omics}")
    return mappings


def map_proteins(reactome_uniprot_file):
    mappings = {}
    reactome_data = get_reactome_data(reactome_uniprot_file)

    reactome_uniprot_ids = reactome_data.keys()

    proteins = Protein.objects.filter(external_id_source='UniProt')
    count_omics = len(proteins)
    count = 0
    for protein in proteins:
        id = protein.external_id
        if id in reactome_uniprot_ids:
            reactome_entries = reactome_data[id]
            mappings[id] = reactome_entries
            for reactome_entry in reactome_entries:
                reactome_mapping_found[reactome_entry['reactome_id']] = True
            # print(f"- {protein.external_id}: {reactome_data[id]}")
            count += 1
    print(f"UniProt-Reactome mappings: {count}/{count_omics}")
    return mappings


def map_metabolites(reactome_chebi_file):
    mappings = {}
    reactome_data = get_reactome_data(reactome_chebi_file)

    reactome_chebi_ids = reactome_data.keys()

    metabolites = Metabolite.objects.filter(external_id_source='ChEBI')
    count_omics = len(metabolites)
    count = 0
    for metabolite in metabolites:
        external_id = metabolite.external_id
        id = external_id.replace('CHEBI_','')
        if id in reactome_chebi_ids:
            reactome_entries = reactome_data[id]
            mappings[id] = reactome_entries
            for reactome_entry in reactome_entries:
                reactome_mapping_found[reactome_entry['reactome_id']] = True
            # print(f"- {metabolite.external_id}: {reactome_data[id]}")
            count += 1
    print(f"ChEBI-Reactome mappings: {count}/{count_omics}")
    return mappings


def compare_ens_uniprot_mappings(gene_mappings,protein_mappings):
    gene_ids = gene_mappings.keys()
    protein_ids = protein_mappings.keys()
    proteins_ens = Protein.objects.only('external_id','gene__external_id').filter(gene__isnull=False)
    count_pr_with_ensg = len(proteins_ens)
    count_asso = 0
    count_ok = 0
    count_partial_ok = 0
    for protein_ens in proteins_ens:
        uniprot_id = protein_ens.external_id
        ensg_id = protein_ens.gene.external_id
        if uniprot_id in protein_ids and ensg_id in gene_ids:
            count_asso +=1
            pr_pathways = sorted([x['reactome_name'] for x in protein_mappings[uniprot_id]])
            gene_pathways = sorted([x['reactome_name'] for x in gene_mappings[ensg_id]])
            if pr_pathways == gene_pathways:
                count_ok +=1
            else:
                count_pathways = 0
                for pathway in pr_pathways:
                    if pathway in gene_pathways:
                        count_pathways += 1
                if count_pathways > 0:
                    count_partial_ok += 1
                print(f'- {ensg_id}-{uniprot_id}: {count_pathways}/{len(pr_pathways)}')
                print(f'  # PROT: {pr_pathways}')
                print(f'  # GENE: {gene_pathways}')

    print(f'count_pr_with_ensg: {count_pr_with_ensg}')
    print(f'Matching pathways: {count_ok}/{count_asso}')
    print(f'Matching pathways - partial: {count_partial_ok}')

# Command line:
# python manage.py runscript get_reactome_mappings --script-args <pat_to_data_directory>
def run(*args):

    if args:
        reactome_dir = args[0]
    else:
        reactome_dir = default_reactome_dir

    reactome_chebi_file = f'{reactome_dir}/ChEBI2Reactome_LOW_Levels_human.txt'
    # reactome_chebi_file = f'{reactome_dir}/ChEBI2Reactome_All_Levels.txt'
    reactome_ensembl_file = f'{reactome_dir}/Ensembl2Reactome_LOW_Levels_human.txt'
    # reactome_uniprot_file = f'{reactome_dir}/UniProt2Reactome_LOW_Levels_human.txt'

    # Web services: https://reactome.org/ContentService/data/pathways/top/9606
    reactome_top_level_file = f'{reactome_dir}/human_top_level.json'
    # 'Pathways hierarchy relationship' => https://reactome.org/download/current/ReactomePathwaysRelation.txt
    reactome_relation_file = f'{reactome_dir}/ReactomePathwaysRelation.txt' 

    # Check files
    if not os.path.isdir(reactome_dir):
        print("Directory '"+reactome_dir+"' can't be found")
        exit(1)
    if not os.path.isfile(reactome_chebi_file):
        print("Reactome-ChEBI file '"+reactome_chebi_file+"' can't be found")
        exit(1)
    if not os.path.isfile(reactome_ensembl_file):
        print("Reactome-Ensembl file '"+reactome_ensembl_file+"' can't be found")
        exit(1)
    if not os.path.isfile(reactome_top_level_file):
        print("Reactome Top Level file '"+reactome_top_level_file+"' can't be found")
        exit(1)
    if not os.path.isfile(reactome_relation_file):
        print("Reactome relation file '"+reactome_relation_file+"' can't be found")
        exit(1)

    mapped_genes = None
    mapped_metabolites = None
    get_top_levels_list(reactome_top_level_file)
    # mapped_genes = map_genes(reactome_ensembl_file)
    # mapped_proteins = map_proteins(reactome_uniprot_file)
    mapped_metabolites = map_metabolites(reactome_chebi_file)
    get_relations(reactome_relation_file)
    print(f"REACTOME ENTITIES: {len(reactome_entities.keys())}")
    print(f"REACTOME LOW TO TOP: {len(reactome_low_to_top_level.keys())}")
    count_low = 0
    for entity in reactome_entities.keys():
        if entity in reactome_low_to_top_level.keys():
            count_low += 1
        else:
            print(f">> MISSING LOW ENTITY: {entity}")
    print(f"COUNT MATCHING LOW ENTITIES: {count_low}")
    # import_reactome_entries(mapped_genes,mapped_metabolites)
    import_reactome_entries()

    if (mapped_genes):
        print(f"- Import Gene mappings ({len(mapped_genes.keys())})")
        # for gene_id in mapped_genes.keys():
        #   gene = Gene.objects.prefetch_related('pathways').get(external_id=gene_id)
        #   existing_gene_reactome_ids = [x.external_id for x in gene.pathways.all()]
        #   reactome_ids = [x['reactome_id'] for x in mapped_genes[gene_id]]
        genes = Gene.objects.prefetch_related('pathways').filter(external_id__in=mapped_genes.keys())
        for gene in genes:
            existing_gene_reactome_ids = [x.external_id for x in gene.pathways.all()]
            reactome_ids = [x['reactome_id'] for x in mapped_genes[gene.external_id]]
            reactome_pathways = Pathway.objects.defer('superpathways').filter(external_id__in=reactome_ids)
            for reactome_pathway in reactome_pathways:
                if reactome_pathway.external_id not in existing_gene_reactome_ids:
                    gene.pathways.add(reactome_pathway)
            gene.save()

     
    if (mapped_metabolites):
        print(f"- Import Metabolite mappings ({len(mapped_metabolites.keys())})")
        # for metabolite_id in mapped_metabolites.keys():
        #     metabolite = Metabolite.objects.prefetch_related('pathways').get(external_id=metabolite_id)
        #     existing_metabolite_reactome_ids = [x.external_id for x in metabolite.pathways.all()]
        #     reactome_ids = [x['reactome_id'] for x in mapped_metabolites[metabolite_id]]
        metabolites = Metabolite.objects.prefetch_related('pathways').filter(external_id__in=mapped_metabolites.keys())
        for metabolite in metabolites:
            existing_metabolite_reactome_ids = [x.external_id for x in metabolite.pathways.all()]
            reactome_ids = [x['reactome_id'] for x in mapped_metabolites[metabolite.external_id]]
            reactome_pathways = Pathway.objects.defer('superpathways').filter(external_id__in=reactome_ids)
            for reactome_pathway in reactome_pathways:
                if reactome_pathway.external_id not in existing_metabolite_reactome_ids:
                    metabolite.pathways.add(reactome_pathway)
            metabolite.save()
#    compare_ens_uniprot_mappings(mapped_genes,mapped_proteins)
        
    # Add cleanup code to remove the Reactome entries not linked to Metabolites nor Genes ? 