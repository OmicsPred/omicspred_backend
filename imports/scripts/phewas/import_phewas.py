import os
import gzip
import csv
import sqlite3
from django.db.models import Q
from imports.config import phewas_publication_id, phewas_method, phewas_csv_dir, efo_sqlite_filepath
from omicspred.models import Cohort, Dataset, Phenotype, Sample, Score, ScorePheWAS


missing_phenotypes_in_db = []
inverted_phenotype_mappings = {}
phecode_labels = {}

traits_to_skip = ['disease','injury']
traits_not_to_split = ['localized superficial swelling, mass, or lump']
adj_pval_threshold = 0.05
source_pmid = 39024449

def select_phenotype_file(dataset_id:str,phenotypes_files_list:list) -> str|None:
    for phenotypes_file in phenotypes_files_list:
        if phenotypes_file.startswith(dataset_id):
            return phenotypes_file
    return None


def fetch_cohort_model():
    try:
        cohort_model = Cohort.objects.get(name_short='MVP')
    except Cohort.DoesNotExist:
        cohort_model = Cohort(
            name_short= 'MVP',
            name_full= 'Million Veteran Program',
            url= 'https://www.mvp.va.gov/pwa/'
        )
        cohort_model.save()
    return cohort_model


def fetch_efo_entry(label:str,use_alt:bool=False) -> list|None:
    con = sqlite3.connect(efo_sqlite_filepath)
    cur = con.cursor()
    data = None
    if use_alt:
        cur.execute('SELECT id,replacement_id FROM efo WHERE alt_label = ?', (label,))
        tmp_data = cur.fetchone()
        if tmp_data:
            new_id = tmp_data[1]
            if new_id:
                cur.execute('SELECT id,label,description,url FROM efo WHERE id = ?', (new_id,))
                data = cur.fetchone()
    else:
        cur.execute('SELECT id,label,description,url FROM efo WHERE label = ?', (label,))
        data = cur.fetchone()
    cur.close()
    con.close()
    if data:
        return data
    else:
        return None



def fetch_phenotype_model(phecode:str, efo_trait:str) -> list:
    phenotype_model = None
    try:
        phenotype_model = Phenotype.objects.get(label__iexact=efo_trait)
    except Phenotype.DoesNotExist:
        efo_data = fetch_efo_entry(efo_trait)
        if not efo_data:
            efo_data = fetch_efo_entry(efo_trait,True)
            if not efo_data:
                print(f"    > {phecode}: no entry found for '{efo_trait}'")
        if efo_data:
            phenotype_model = Phenotype(
                id=efo_data[0],
                label=efo_data[1],
                description=efo_data[2],
                url=efo_data[3],
                source='EFO'
            )
            phenotype_model.save()
    except:
        print(f">> ERROR with phenotype label '{efo_trait}' (for PheCode {phecode})")
        exit()
    if phenotype_model:
        efo_id = phenotype_model.id
        if efo_id not in inverted_phenotype_mappings.keys():
            inverted_phenotype_mappings[efo_id] = set()
        inverted_phenotype_mappings[efo_id].add(phecode)
    return phenotype_model


def fetch_score_model(opgs_id:str) -> Score:
    try:
        score_num = opgs_id.replace('OPGS', '').lstrip('0')
        score_model = Score.objects.only('num','id').get(num=score_num)
        return score_model
    except Score.DoesNotExist:
        print(f"    > {opgs_id}: can't find the score in the database")
        exit()


def fetch_sample_model(sample_info:list,gcst_id:str,cohort_model:Cohort) -> Sample:
    sample_number = sample_info[0]
    ancestry = sample_info[1]
    sample_model = None
    try:
        sample_model = Sample.objects.get(
            Q(sample_number=sample_number) & 
            Q(ancestry_broad=ancestry) & 
            Q(source_gwas_catalog=gcst_id) &
            Q(source_pmid=source_pmid)
        )
    except Sample.DoesNotExist:
        sample_model = Sample(
            sample_number = sample_number,
            ancestry_broad = ancestry,
            source_gwas_catalog = gcst_id,
            source_pmid = source_pmid,
        )
        sample_model.save()
        sample_model.cohorts.add(cohort_model)
        sample_model.save()
    return sample_model


def run():
    phe_files = []
    for p_file in os.listdir(phewas_csv_dir):
        if p_file.endswith('.csv.gz'):
            phe_files.append(p_file)

    cohort_model = fetch_cohort_model()

    phenotype_models_dict = {}
    sample_models_dict = {}

    # For each dataset
    count_datasets = 0
    # datasets = Dataset.objects.filter(publication_id=phewas_publication_id)
    datasets = Dataset.objects.filter(id='OPD000215')
    # datasets = Dataset.objects.filter(id__in=['OPD000001','OPD000003','OPD000004','OPD000005']).order_by('id')
    for dataset in datasets:
        dataset_id = dataset.id
        count_datasets += 1
        print(f"# Dataset {dataset_id} ({count_datasets}/{len(datasets)})")

        phenotype_file = select_phenotype_file(dataset_id,phe_files)
        if not phenotype_file:
            print("  > ERROR: can't find a phenotype file for the dataset {dataset_id}")
            exit()
        
        count_rows = 0
        count_skipped = 0
        with gzip.open(f'{phewas_csv_dir}/{phenotype_file}','rt') as f:
            csv_reader = csv.DictReader(f,delimiter=',')
            for row in csv_reader:
                count_rows += 1
                # if str(count_rows).endswith('00000') or str(count_rows).endswith('50000'):
                if str(count_rows).endswith('00000'):
                    print(f'  - {count_rows} done')

                ## Parse row ##
                # Main IDs
                opgs_id = row['OmicsPred ID']
                phecode = row['PheCode']

                # Data values
                zscore = row['zscore']
                pvalue = row['pvalue']
                adjusted_pvalue = row['fdr']
                fdr_sign = row['fdr_sig']
                bonferroni = row['bonferroni']
                effect_size = row['effect_size']
                var_gene_exp = row['var_g']
                variants_number_used = row['n_snps_used']
                variants_fraction_found = row['FractionSNPs_Found']

                # Adjusted P-value filter
                if adjusted_pvalue:
                    adjusted_pvalue = float(adjusted_pvalue)
                if adjusted_pvalue >= adj_pval_threshold or fdr_sign != 'TRUE':
                    count_skipped += 1
                    continue

                # Metadata
                sample_info = row['discoverySampleAncestry'].split(' ',1)
                trait_reported = row['reportedTrait']
                gcst_id = row['GWASCatalogue_accessionId']

                # Trait(s) / Phenotype(s)
                if phecode:
                    phecode = phecode.replace('PheCode','')
                    phecode_label = trait_reported.split(' (')[0]
                    phecode_labels[phecode] = phecode_label
                efo_traits = row['efoTraits']
                if efo_traits in traits_not_to_split:
                    efo_traits_list = [efo_traits]
                else:
                    efo_traits_list = row['efoTraits'].split(',')

                phenotype_models = []
                for efo_trait in efo_traits_list:
                    if efo_trait in traits_to_skip and len(efo_traits_list) > 1:
                        continue
                    if efo_trait in phenotype_models_dict.keys():
                        phenotype_models.append(phenotype_models_dict[efo_trait])
                    else:
                        phenotype_model = fetch_phenotype_model(phecode,efo_trait)
                        if phenotype_model:
                            phenotype_models_dict[efo_trait] = phenotype_model
                            phenotype_models.append(phenotype_model)
                        else:
                            print(f"    -> Can't create phenotype for {opgs_id} ({efo_trait})")
                
                if len(phenotype_models) == 0:
                    print(f"    -> Can't find phenotype for {opgs_id} ({efo_traits_list})")

                ## Models ##
                # Score model
                score_model = fetch_score_model(opgs_id)
                
                # Sample model
                sample_model = None
                sample_key = f'{'_'.join(sample_info)}_{gcst_id}_{source_pmid}'
                if sample_key in sample_models_dict.keys():
                    sample_model = sample_models_dict[sample_key]
                else:
                    sample_model = fetch_sample_model(sample_info,gcst_id,cohort_model)
                    sample_models_dict[sample_key] = sample_model

                # Score_PheWAS model
                score_phewas_model = ScorePheWAS(
                    score = score_model,
                    dataset = dataset,
                    publication_id = phewas_publication_id,
                    method_description = phewas_method,
                    trait_reported = trait_reported,
                    zscore = zscore,
                    pvalue = pvalue,
                    adjusted_pvalue = adjusted_pvalue,
                    bonferroni = bonferroni,
                    effect_size = effect_size,
                    var_gene_exp = var_gene_exp,
                    variants_number_used = variants_number_used,
                    variants_fraction_found = variants_fraction_found
                )
                score_phewas_model.save()

                # Add Sample models
                # FOR NOW ONLY IMPORT 1 SAMPLE PER ScorePheWAS
                score_phewas_model.samples.add(sample_model)
                # Add Phenotype models
                for phenotype_model in phenotype_models:
                    score_phewas_model.phenotypes.add(phenotype_model)
                score_phewas_model.save()
        
        # Update 'phenotypes_count' in Dataset model
        print(f"  > Update 'phenotypes_count' in Dataset")
        score_phewas_count = ScorePheWAS.objects.filter(dataset=dataset).count()
        dataset.phewas_count = score_phewas_count
        dataset.save()

        print(f"  > Skipped rows: {count_skipped}/{count_rows}")
    
    # Update 'trait_reported' column in Phenotype table with inverted_phenotype_mappings
    print("\n# Update mapped phecodes to EFOs")
    # [
    #     {
    #         "id": "172",
    #         "label": "Skin cancer",
    #         "source": "PheCode"
    #     },
    #     {
    #         "id": "172.2",
    #         "label": "Other non-epithelial cancer of skin",
    #         "source": "PheCode"
    #     }
    # ]
    for efo_id in inverted_phenotype_mappings.keys():
        try:
            phenotype_model = Phenotype.objects.get(id=efo_id)
            current_trait_reported = phenotype_model.traits_reported
            mapped_list = []
            if current_trait_reported:
                mapped_list = [x['id'] for x in current_trait_reported]
            else:
                current_trait_reported = []
            for phecode in inverted_phenotype_mappings[efo_id]:
                if phecode not in mapped_list:
                    phecode_reported = {
                        "id": phecode,
                        "label": phecode_labels[phecode],
                        "source": "PheCode"
                    }
                    current_trait_reported.append(phecode_reported)
            phenotype_model.traits_reported=current_trait_reported
            phenotype_model.save()
        except Phenotype.DoesNotExist:
            print(f"    -> Can't find phenotype model for '{efo_id}'")
    
    phenotypes = Phenotype.objects.all().prefetch_related('phenotype_scores')

    for phenotype in phenotypes:
        phewas_count = phenotype.phenotype_scores.count()
        phenotype.phewas_count = phewas_count
        phenotype.save()



