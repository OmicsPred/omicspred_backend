import os
import pandas as pd
from datetime import date
from omicspred.models import *
from exports.exports import PGSExport, fields_to_export

exports_dir = '/Users/lg10/Workspace/datafiles/OmicsPred/metadata_exports'
file_url_prefix = 'https://app.box.com/s/'

nested_attr_sep = '__'

def get_data_attr(model:object,model_type:str)-> dict:
    export_data = {}
    for field in fields_to_export[model_type]:
        # Skip the ManyToMany relations and the non native fields
        if 'skip_auto_import' in field.keys():
            continue
        field_name = field['name']
        if nested_attr_sep in field_name:
            attrs = field_name.split(nested_attr_sep)
            nested_model = getattr(model,attrs[0])
            value = getattr(nested_model,attrs[1])
            export_data[field_name] = value
        else:
            export_data[field_name] = getattr(model, field_name)
        # Date format
        data_value = export_data[field_name]
        if isinstance(data_value, date):
            export_data[field_name] = data_value.strftime('%m/%d/%Y')
        # print(f'{field_name}: {export_data[field_name]} | {type(export_data[field_name])}')
    return export_data


def get_molecular_traits(mt_models:list,mt_type:str,score_data:dict) -> dict:
    mt_dict = {
        'external_id': [],
        'name': []
    }
    for mt_model in mt_models:
        mt_data = get_data_attr(mt_model,'MolecularTrait')
        for field in mt_dict.keys():
            if mt_data[field]:
                mt_dict[field].append(mt_data[field])
    for field in mt_dict.keys():
        score_data[f'{mt_type}__{field}'] = ','.join(mt_dict[field])
    return score_data


def run():

    # datasets = Dataset.objects.all().order_by('num')
    datasets = Dataset.objects.filter(num=1).order_by('num')
    print("## Start metadata exports, dataset by dataset")
    datasets_total = len(datasets)
    count_dataset = 0
    for dataset in datasets:
        count_dataset += 1
        dataset_id = dataset.id
        print(f"- Dataset {dataset_id} ({count_dataset}/{datasets_total})")
        # Prepare data for exports
        data = { 
            'dataset': get_data_attr(dataset,'Dataset'),
            'publication': get_data_attr(dataset.publication,'Publication'),
            'scores': [],
            'performances': [],
            'cohorts': []
        }

        # /!\ TODO: add files url to dataset
        files_ids_dict = dataset.files_ids
        for file in files_ids_dict.keys():
            data['dataset'][f'file_url_{file}'] = f'{file_url_prefix}{files_ids_dict[file]}'
        
        # Prepare cohort data
        cohorts_names = set()
        cohorts_data = []
        for t_sample in dataset.samples_training.all():
            cohorts = t_sample.cohorts.all().order_by('name_short')
            for cohort in cohorts:
                if cohort.name_short not in cohorts_names:
                    cohorts_data.append(get_data_attr(cohort,'Cohort'))
                    cohorts_names.add(cohort.name_short)
        for v_sample in dataset.samples_validation.all():
            cohorts = v_sample.cohorts.all().order_by('name_short')
            for cohort in cohorts:
                if cohort.name_short not in cohorts_names:
                    cohorts_data.append(get_data_attr(cohort,'Cohort'))
                    cohorts_names.add(cohort.name_short)
        data['cohorts'] = cohorts_data

        # Prepare score data
        scores = dataset.dataset_score.all().order_by('num')
        for score in scores:
            # Prepare score data
            score_data = get_data_attr(score,'Score')
            # Genes
            score_data = get_molecular_traits(score.genes.all(),'genes',score_data)
            # Proteins
            score_data = get_molecular_traits(score.proteins.all(),'proteins',score_data)
            # Metabolites
            score_data = get_molecular_traits(score.metabolites.all(),'metabolites',score_data)
            
            data['scores'].append(score_data)

            # Prepare performances (metrics, samples, cohorts)
            for perf in score.score_performance.all().order_by('id'):
                sample_perf_data = get_data_attr(perf,'Performance')
                # Update eval_type using the long name
                sample_perf_data['eval_type'] = perf.get_eval_type_display()

                # Cohorts
                cohorts_list = []
                for cohort in perf.sample.cohorts.all():
                    cohorts_list.append(cohort.name_short)
                sample_perf_data['cohorts'] = ','.join(sorted(cohorts_list))

                # Metrics
                metrics_data = {
                    'metrics_r2': None,
                    'metrics_r2_pval': None,
                    'metrics_rho': None,
                    'metrics_rho_pval': None,
                    'metrics_match_rate': None
                }
                for metric in perf.performance_metric.all():
                    m_name = metric.name_short
                    if m_name == 'R2':
                        metrics_data['metrics_r2'] = metric.estimate
                        metrics_data['metrics_r2_pval'] = metric.pvalue
                    elif m_name == 'Rho':
                        metrics_data['metrics_rho'] = metric.estimate
                        metrics_data['metrics_rho_pval'] = metric.pvalue
                    elif m_name == 'Match Rate':
                        metrics_data['metrics_match_rate'] = metric.estimate
                if sample_perf_data['eval_type'] == 'Training':
                    metrics_data['metrics_match_rate'] = 1
                for md in metrics_data.keys():
                    sample_perf_data[md] = metrics_data[md]

                data['performances'].append(sample_perf_data)
            
        #     for dtype in data.keys():
        #         print(f'# {dtype}:\n{data[dtype]}')
            # exit()

        # Create export
        filename = f'{exports_dir}/{dataset_id}_metadata.xlsx'
        op_export = PGSExport(filename, data, dataset_id)
        op_export.generate_sheets()
        op_export.save()
        # print(data)