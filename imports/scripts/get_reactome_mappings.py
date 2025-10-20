import os, csv, json
from omicspred.models import Gene,Metabolite,Pathway,SuperPathway

default_reactome_dir = '/Users/lg10/Workspace/datafiles/OmicsPred/Reactome'

reactome_entities = {}
reactome_top_level = {}
reactome_top_level_synonyms = {}
reactome_low_to_top_level = {}
reactome_mapping_found = {}

pathway_source = 'Reactome'
external_metabolite_source = 'ChEBI'

legacy_pathway_mappings = {
    'Alanine and Aspartate Metabolism': [
        {'reactome_id': 'R-HSA-8964540', 'reactome_name': 'Alanine metabolism'},
        {'reactome_id': 'R-HSA-8963693', 'reactome_name':'Aspartate and asparagine metabolism'}
    ],
    'Creatine Metabolism': [
        {'reactome_id': 'R-HSA-71288', 'reactome_name': 'Creatine metabolism'}
    ],
    'Glutamate Metabolism': [
        {'reactome_id': 'R-HSA-8964539', 'reactome_name': 'Glutamate and glutamine metabolism'}
    ],
    'Glutathione Metabolism': [
        {'reactome_id': 'R-HSA-174403', 'reactome_name': 'Glutathione synthesis and recycling'}
    ],
    'Phenylalanine and Tyrosine Metabolism': [
        {'reactome_id': 'R-HSA-8963691', 'reactome_name': 'Phenylalanine and tyrosine metabolism'}
    ],
    'Polyamine Metabolism': [
        {'reactome_id': 'R-HSA-351202', 'reactome_name': 'Metabolism of polyamines'}
    ],
    'Glycogen Metabolism': [
        {'reactome_id': 'R-HSA-8982491', 'reactome_name': 'Glycogen metabolism'}
    ],
    'Glycolysis, Gluconeogenesis, and Pyruvate Metabolism': [
        {'reactome_id': 'R-HSA-70171', 'reactome_name': 'Glycolysis'},
        {'reactome_id': 'R-HSA-70263', 'reactome_name': 'Gluconeogenesis'},
        {'reactome_id': 'R-HSA-70268', 'reactome_name': 'Pyruvate metabolism'}
    ],
    'Ascorbate and Aldarate Metabolism': [
        {'reactome_id': 'R-HSA-70268', 'reactome_name': 'Vitamin C (ascorbate) metabolism'}
    ],
    'Hemoglobin and Porphyrin Metabolism': [
        {'reactome_id': 'R-HSA-189445', 'reactome_name': 'Metabolism of porphyrins'}
    ],
    'Nicotinate and Nicotinamide Metabolism': [
        {'reactome_id': 'R-HSA-196807', 'reactome_name': 'Nicotinate metabolism'}
    ],
    'Pantothenate and CoA Metabolism': [
        {'reactome_id': 'R-HSA-199220', 'reactome_name': 'Vitamin B5 (pantothenate) metabolism'}
    ],
    'Riboflavin Metabolism': [
        {'reactome_id': 'R-HSA-196843', 'reactome_name': 'Vitamin B2 (riboflavin) metabolism'}
    ],
    'TCA Cycle': [
        {'reactome_id': 'R-HSA-71403', 'reactome_name': 'Citric acid cycle (TCA cycle)'}
    ],
    'Fatty Acid Synthesis': [
        {'reactome_id': 'R-HSA-8978868', 'reactome_name': 'Fatty acid metabolism'}
    ],
    'Ketone bodies': [
        {'reactome_id': 'R-HSA-74182', 'reactome_name': 'Ketone body metabolism'}
    ],
    'Phospholipid Metabolism': [
        {'reactome_id': 'R-HSA-1483257', 'reactome_name': 'Phospholipid metabolism'}
    ],
    'Sphingolipid Metabolism': [
        {'reactome_id': 'R-HSA-428157', 'reactome_name': 'Sphingolipid metabolism'}
    ],
    'Steroid': [
        {'reactome_id': 'R-HSA-8957322', 'reactome_name': 'Metabolism of steroids'}
    ]
}


def get_top_levels_list(reactome_top_level_file:str) -> None:
    ''' Retrieve the list of top level Reactome entities '''
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


def get_relations(reactome_relation_file:str) -> None:
    ''' Store the Reactome child->parent associations '''
    with open(reactome_relation_file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        tmp_relation = {}
        # Store child->parent association
        for row in reader:
            parent = row[0]
            child = row[1]
            if not parent.startswith('R-HSA-'):
                continue
            if child in tmp_relation.keys():
                tmp_relation[child].append(parent)
            else:
                tmp_relation[child] = [parent]
        # Store top level for each low level (i.e. child)
        for pathway in tmp_relation.keys():
            top_levels_list = fetch_top_level(tmp_relation,pathway,set())
            if top_levels_list:
                # top_level = [ reactome_top_level[x] for x in top_levels_list]
                # print(f'{pathway}: {" | ".join(top_level)}')
                reactome_low_to_top_level[pathway] = list(top_levels_list)


def fetch_top_level(relation_list:dict,pathway:str,top_levels_list:set) -> set:
    ''' Fetch the top level Reactome entities associated with a given low level entity '''
    for parent in relation_list[pathway]:
        if parent in reactome_top_level.keys():
            top_levels_list.add(parent)
            return top_levels_list
        else:
            top_levels_list = fetch_top_level(relation_list,parent,top_levels_list)
    return top_levels_list


def get_reactome_data(file:str) -> dict:
    ''' Extract and store the Reactome / External source associations and data '''
    reactome_data = {}
    with open(file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        # next(reader, None)  # skip the headers
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


def import_reactome_entries() -> None:
    ''' Import the Reactome entities and their superpathways into the DB '''
    reactome_low_top_ids = reactome_low_to_top_level.keys()
    mapped_reactome_ids = reactome_mapping_found.keys()
    for entity_id in reactome_entities.keys():
        id = entity_id
        name = reactome_entities[entity_id]
        if id in mapped_reactome_ids:
            try:
                # Check if Reactome entry already in DB
                pathway = Pathway.objects.get(external_id=id)
                # Check superpathways
                if id in reactome_low_top_ids:
                    # Get current pathway-superpathway associations in the DB
                    current_superpathway_ids = [ x.external_id for x in pathway.superpathways.all()]
                    linked_superpathways = []
                    for superpathway_id in reactome_low_to_top_level[id]:
                        try:
                            superpathway = SuperPathway.objects.get(external_id=superpathway_id)
                            linked_superpathways.append(superpathway)
                        except SuperPathway.DoesNotExist:
                            print("!! Can't find the superpathway {superpathway_id} in the DB")
                    # Add new superpathways (if there are)
                    if linked_superpathways:
                        for superpathway in linked_superpathways:
                            if superpathway.external_id not in current_superpathway_ids:
                                pathway.superpathways.add(superpathway)
                        pathway.save()
            except Pathway.DoesNotExist:
                # Add new Reactome entry
                pathway = Pathway(external_id=id,name=name,external_id_source=pathway_source)
                pathway.save()
                # Add pathway-superpathway associations
                if id in reactome_low_top_ids:
                    linked_superpathways = []
                    for superpathway_id in reactome_low_to_top_level[id]:
                        try:
                            superpathway = SuperPathway.objects.get(external_id=superpathway_id)
                            linked_superpathways.append(superpathway)
                        except SuperPathway.DoesNotExist:
                            print("!! Can't find the superpathway {superpathway_id} in the DB")
                    if linked_superpathways:
                        for superpathway in linked_superpathways:
                            pathway.superpathways.add(superpathway)
                        pathway.save()


def map_genes(reactome_ensembl_file:str) -> dict:
    ''' Extract the association Gene-Reactome, using IDs and DB models '''
    external_source = 'Ensembl'
    reactome_data = get_reactome_data(reactome_ensembl_file)
    genes = Gene.objects.filter(external_id_source=external_source)
    return get_mappings(genes,reactome_data,external_source)


# def map_proteins(reactome_uniprot_file:str) -> dict:
#     ''' Extract the association Protein-Reactome, using IDs and DB models '''
#     external_source = 'UniProt'
#     reactome_data = get_reactome_data(reactome_uniprot_file)
#     proteins = Protein.objects.filter(external_id_source=external_source)
#     return get_mappings(proteins,reactome_data,external_source)


def map_metabolites(reactome_chebi_file:str) -> dict:
    ''' Extract the association Metabolite-Reactome, using IDs and DB models '''
    reactome_data = get_reactome_data(reactome_chebi_file)
    metabolites = Metabolite.objects.filter(external_id_source=external_metabolite_source)
    return get_mappings(metabolites,reactome_data,external_metabolite_source)


def map_legacy_metabolites_pathways() -> dict:
    metabolites = Metabolite.objects.select_related('pathway_group','pathway_subgroup').exclude(external_id_source=external_metabolite_source).prefetch_related('pathways')
    return get_legacy_metabolite_mappings(metabolites)


def get_mappings(molecular_traits:list,reactome_data:dict,source:str) -> dict:
    ''' Build the association Metabolite-Reactome, using IDs and DB models '''
    mappings = {}
    reactome_trait_ids = reactome_data.keys()
    count_omics = len(molecular_traits)
    count = 0
    for molecular_trait in molecular_traits:
        external_id = molecular_trait.external_id
        id = external_id.replace('CHEBI_','')
        if id in reactome_trait_ids:
            reactome_entries = reactome_data[id]
            # Add Reactome ID to the list of entries found
            for reactome_entry in reactome_entries:
                reactome_mapping_found[reactome_entry['reactome_id']] = True
            # print(f"- {molecular_trait.external_id}: {reactome_data[id]}")
            # Add mapping
            mappings[id] = reactome_entries
            count += 1
    print(f"{source}-Reactome mappings: {count}/{count_omics}")
    return mappings


def get_legacy_metabolite_mappings(metabolites:list) -> dict:
    mappings = {}
    for metabolite in metabolites:
        if metabolite.external_id_source != 'ChEBI':
            op_pathway = metabolite.pathway_subgroup
            if op_pathway in legacy_pathway_mappings.keys():
                reactome_entries = legacy_pathway_mappings[op_pathway]
                # Add Reactome ID to the list of entries found
                for reactome_entry in reactome_entries:
                    reactome_mapping_found[reactome_entry['reactome_id']] = True
                mappings[metabolite.id] = reactome_entries
    return mappings


def add_protein_mappings():
    print('\n# Import Protein mappings')
    genes = Gene.objects.prefetch_related('pathways').filter(pathways__isnull=False).prefetch_related('gene_protein').distinct()
    count_proteins = 0
    for gene in genes:
        proteins = gene.gene_protein.all()
        if len(proteins):
            pathways = gene.pathways.all()
            for protein in proteins:
                count_proteins += 1
                print_progress(count_proteins,'protein')
                # Reset all the protein/pathway relations
                protein.pathways.clear()
                protein.pathways.add(*pathways)
    print(f">> Proteins with pathway: {count_proteins}")


def detect_non_associated_pathways():
    pathways = Pathway.objects.all().prefetch_related('pathway_metabolites', 'pathway_proteins', 'pathway_genes')
    count = 0
    for pathway in pathways:
        has_asso = False
        if pathway.pathway_genes.count():
            has_asso = True
        elif pathway.pathway_metabolites.count():
            has_asso = True

        if has_asso == False:
            children_pathways = Pathway.objects.filter(parent_external_id__icontains=pathway.external_id)
            if len(children_pathways) > 0:
                print(f"- {pathway.external_id} ({pathway.name}) is not associated with a molecular trait - but is a parent of {len(children_pathways)} pathway(s)")
            else:
                print(f"- {pathway.external_id} ({pathway.name}) is not associated with a molecular trait")
            count += 1
    print(f">>> Non associated pathways: {count}")


def update_top_level_flag():
    superpathway_ids= SuperPathway.objects.values_list('external_id')
    # Update all pathways to false
    Pathway.objects.all().update(top_level=False)
    # Update the top_level pathways
    Pathway.objects.filter(external_id__in=superpathway_ids).update(top_level=True)


def update_parent_external_id(reactome_parent_child_file:str):
    child_parent = {}
    with open(reactome_parent_child_file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        # child->parent association
        for row in reader:
            parent = row[0]
            child = row[1]
            if not parent.startswith('R-HSA-'):
                continue
            # Update parent_id
            if child not in child_parent.keys():
                child_parent[child] = set()
            child_parent[child].add(parent)

    for child_pathway in child_parent.keys():
        parent = '|'.join(child_parent[child_pathway])
        Pathway.objects.filter(external_id=child_pathway).update(parent_external_id=parent)

    # Check that all parents have a pathway entry in OmicsPred
    external_ids = Pathway.objects.values_list('external_id')
    parent_external_ids = Pathway.objects.values_list('parent_external_id').filter(parent_external_id__isnull=False).distinct()
    for parent_external_tuple in parent_external_ids:
        parent_external_id = parent_external_tuple[0]

        for parent_id in parent_external_id.split('|'):
            if (parent_id,) not in external_ids:
                print(f"- ERROR: parent external ID '{parent_id}' hasn't a Pathway entry in OmicsPred")


def get_reactome_models() -> dict:
    reactome_pathways = {}
    reactome_pathway_models = Pathway.objects.defer('superpathways').all()
    for reactome_pathway_model in reactome_pathway_models:
        reactome_pathways[reactome_pathway_model.external_id] = reactome_pathway_model
    return reactome_pathways


def print_progress(count:int,mt_type:str):
    if str(count).endswith('000'):
        print(f"- {count} {mt_type}s done")

# def compare_ens_uniprot_mappings(gene_mappings:dict,protein_mappings:dict) -> None:
#     ''' Compare Gene-Reactome associations with the Protein-Reactome associations, using the associations Gene-Protein '''
#     gene_ids = gene_mappings.keys()
#     protein_ids = protein_mappings.keys()
#     proteins_ens = Protein.objects.only('external_id','gene__external_id').filter(gene__isnull=False)
#     count_pr_with_ensg = len(proteins_ens)
#     count_asso = 0
#     count_ok = 0
#     count_partial_ok = 0
#     for protein_ens in proteins_ens:
#         uniprot_id = protein_ens.external_id
#         ensg_id = protein_ens.gene.external_id
#         if uniprot_id in protein_ids and ensg_id in gene_ids:
#             count_asso +=1
#             pr_pathways = sorted([x['reactome_name'] for x in protein_mappings[uniprot_id]])
#             gene_pathways = sorted([x['reactome_name'] for x in gene_mappings[ensg_id]])
#             if pr_pathways == gene_pathways:
#                 count_ok +=1
#             else:
#                 count_pathways = 0
#                 for pathway in pr_pathways:
#                     if pathway in gene_pathways:
#                         count_pathways += 1
#                 if count_pathways > 0:
#                     count_partial_ok += 1
#                 print(f'- {ensg_id}-{uniprot_id}: {count_pathways}/{len(pr_pathways)}')
#                 print(f'  # PROT: {pr_pathways}')
#                 print(f'  # GENE: {gene_pathways}')

#     print(f'count_pr_with_ensg: {count_pr_with_ensg}')
#     print(f'Matching pathways: {count_ok}/{count_asso}')
#     print(f'Matching pathways - partial: {count_partial_ok}')


##########################################################################################

# Command line:
# python manage.py runscript get_reactome_mappings --script-args <path_to_data_directory>
def run(*args):

    if args:
        reactome_dir = args[0]
    else:
        reactome_dir = default_reactome_dir

    # Files in https://reactome.org/download/current/
    # Low level
    # reactome_chebi_file = f'{reactome_dir}/ChEBI/ChEBI2Reactome_LOW_Levels_human.txt'
    # reactome_ensembl_file = f'{reactome_dir}/Ensembl/Ensembl2Reactome_LOW_Levels_human.txt'
    # All levels
    reactome_chebi_file = f'{reactome_dir}/ChEBI/ChEBI2Reactome_All_Levels_human.txt'
    reactome_ensembl_file = f'{reactome_dir}/Ensembl/Ensembl2Reactome_All_Levels_human_ensg.txt'

    # reactome_uniprot_file = f'{reactome_dir}/UniProt/UniProt2Reactome_LOW_Levels_human.txt'

    # Web services: https://reactome.org/ContentService/data/pathways/top/9606
    reactome_top_level_file = f'{reactome_dir}/human_top_level.json'
    # Pathways hierarchy relationship => https://reactome.org/download/current/ReactomePathwaysRelation.txt
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

    # Get list of top level Reactome entities
    get_top_levels_list(reactome_top_level_file)

    # Proteins mappings
    # mapped_proteins = map_proteins(reactome_uniprot_file)

    # Extract child-parent relations
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

    # Get mappings
    mapped_genes = map_genes(reactome_ensembl_file)
    mapped_metabolites = map_metabolites(reactome_chebi_file)
    legacy_mapped_metabolites = map_legacy_metabolites_pathways()

    # Import Reactome data
    import_reactome_entries()

    # Fetch all the Reactome models
    reactome_pathways = get_reactome_models()

    # Genes mappings
    if mapped_genes:
        print(f"\n# Import Gene mappings ({len(mapped_genes.keys())})")
        count_gene_done = 0
        genes = Gene.objects.prefetch_related('pathways').filter(external_id__in=mapped_genes.keys()).prefetch_related('gene_protein').distinct()
        for gene in genes:
            print_progress(count_gene_done,'gene')
            # Remove the former list of Gene-Pathway asssociations
            gene.pathways.clear()
            # Get Reactome IDs from existing associations
            reactome_ids = [x['reactome_id'] for x in mapped_genes[gene.external_id]]
            # Add new Reactome associations when found
            new_gene_reactome = []
            for reactome_id in reactome_ids:
                try:
                    new_gene_reactome.append(reactome_pathways[reactome_id])
                except Exception as e:
                    print(f"Can't create the association between the Reactome entry {reactome_id} and the gene {gene.external_id}: {e}")
            gene.pathways.add(*new_gene_reactome)
            # Add Protein-Reactome associations (via the Gene)
            proteins = gene.gene_protein.all()
            if len(proteins):
                for protein in proteins:
                    protein.pathways.add(*new_gene_reactome)
            count_gene_done += 1

    
    # Metabolites mappings
    if mapped_metabolites:
        print(f"\n# Import Metabolite mappings ({len(mapped_metabolites.keys())})")
        count_metabolite_done = 0
        metabolites = Metabolite.objects.prefetch_related('pathways').filter(external_id__in=mapped_metabolites.keys())
        for metabolite in metabolites:
            print_progress(count_metabolite_done,'metabolite')
            # Remove the former list of Metabolite-Pathway asssociations
            metabolite.pathways.clear()
            # Get Reactome IDs from existing associations
            reactome_ids = [x['reactome_id'] for x in mapped_metabolites[metabolite.external_id]]
            # Get Reactome IDs from file associations
            reactome_pathways = Pathway.objects.defer('superpathways').filter(external_id__in=reactome_ids)
            # Add new Reactome associations when found
            new_metabolite_reactome = []
            for reactome_id in reactome_ids:
                try:
                    new_metabolite_reactome.append(reactome_pathways[reactome_id])
                    # reactome_pathway = reactome_pathways[reactome_id]
                    # metabolite.pathways.add(reactome_pathway)
                except Exception as e:
                    print(f"Can't create the association between the Reactome entry {reactome_id} and the metabolite {metabolite.external_id}: {e}")
            metabolite.pathways.add(*new_metabolite_reactome)
            # metabolite.save()
            count_metabolite_done += 1

    # Legacy metabolomic pathways (from the original OmicsPred metabolomics datasets)
    if legacy_mapped_metabolites:
        print(f"\n# Import Legacy Metabolite mappings ({len(legacy_mapped_metabolites.keys())})")
        count_legacy_metabolite_done = 0
        metabolites = Metabolite.objects.prefetch_related('pathways').filter(id__in=legacy_mapped_metabolites.keys())
        for metabolite in metabolites:
            print_progress(count_legacy_metabolite_done,'metabolite')
            # Remove the former list of Metabolite-Pathway asssociations
            metabolite.pathways.clear()
            # Get Reactome IDs from existing associations
            reactome_ids = [x['reactome_id'] for x in legacy_mapped_metabolites[metabolite.id]]
            # Get Reactome IDs from file associations
            reactome_pathways = Pathway.objects.defer('superpathways').filter(external_id__in=reactome_ids)
            # Add new Reactome associations when found
            new_metabolite_reactome = []
            for reactome_id in reactome_ids:
                try:
                    new_metabolite_reactome.append(reactome_pathways[reactome_id])
                except Exception as e:
                    print(f"Can't create the association between the Reactome entry {reactome_id} and the metabolite {metabolite.name}: {e}")
            metabolite.pathways.add(*new_metabolite_reactome)
            # metabolite.save()
            count_legacy_metabolite_done += 1

    # Add Protein mappings
    add_protein_mappings()

    # Update top_level flag
    update_top_level_flag()
    update_parent_external_id(reactome_relation_file)

    # Add cleanup code to remove the Reactome entries not linked to Metabolites nor Genes ?
    detect_non_associated_pathways()

#    compare_ens_uniprot_mappings(mapped_genes,mapped_proteins)
        
