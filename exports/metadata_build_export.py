import os
import sqlite3
from datetime import date
from omicspred.models import *
from exports.exports import OPExport, fields_to_export, dataset_files


class MetadataExport:

    file_url_prefix = 'https://app.box.com/s/'
    nested_attr_sep = '__'

    def __init__(self, exports_dir:str, sqlite_dir:str, dataset:Dataset):
        self.dataset = dataset
        self.dataset_id = dataset.id
        self.sqlite_dir = f'{sqlite_dir}/{self.dataset_id}'
        self.data = {
            'dataset': self.get_data_attr(self.dataset,'Dataset'),
            'publication': self.get_data_attr(self.dataset.publication,'Publication'),
            'scores': [],
            'performances': [],
            'cohorts': []
        }
        self.phi_values = {}
        self.phi_values_keys = []

        # Find corresponding SQLite file
        self.sqlite_file = None
        for s_file in os.listdir(self.sqlite_dir):
            if s_file.startswith(dataset.id) and s_file.endswith('.db'):
                self.sqlite_file = (s_file)
                break
        if not self.sqlite_file:
            print(f"ERROR: Can't find a SQLite file for the dataset {self.dataset_id} in {self.sqlite_dir}")
            exit()

        filename = self.sqlite_file.replace('.db','_metadata.xlsx')
        self.filepath = f'{exports_dir}/{filename}'


    def get_data_attr(self, model:object, model_type:str)-> dict:
        export_data = {}
        for field in fields_to_export[model_type]:
            # Skip the ManyToMany relations and the non native fields
            if 'skip_auto_import' in field.keys():
                continue
            field_name = field['name']
            if self.nested_attr_sep in field_name:
                attrs = field_name.split(self.nested_attr_sep)
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


    def get_molecular_traits(self, mt_models:list, mt_type:str, score_data:dict) -> dict:
        mt_dict = {
            'external_id': [],
            'name': []
        }
        for mt_model in mt_models:
            mt_data = self.get_data_attr(mt_model,'MolecularTrait')
            for field in mt_dict.keys():
                if mt_data[field]:
                    mt_dict[field].append(mt_data[field])
        for field in mt_dict.keys():
            score_data[f'{mt_type}__{field}'] = ','.join(mt_dict[field])
        return score_data


    def build_score_metadata(self, score:Score):
        # Prepare score data
        score_data = self.get_data_attr(score,'Score')
        # Phi value
        if score.id in self.phi_values_keys:
            score_data['phi'] = self.phi_values[score.id]
        else:
            score_data['phi'] = None
        # Genes
        score_data = self.get_molecular_traits(score.genes.all(),'genes',score_data)
        # Proteins
        score_data = self.get_molecular_traits(score.proteins.all(),'proteins',score_data)
        # Metabolites
        score_data = self.get_molecular_traits(score.metabolites.all(),'metabolites',score_data)

        self.data['scores'].append(score_data)


    def build_performance_metadata(self, score:Score):
        # Prepare performances (metrics, samples, cohorts)
        for perf in score.score_performance.all().order_by('id'):
            sample_perf_data = self.get_data_attr(perf,'Performance')
            # Update eval_type using the long name
            sample_perf_data['eval_type'] = perf.get_eval_type_display()

            # Update the Sample ancestry_assignment using the long name
            sample_perf_data['sample__ancestry_assignment'] = perf.sample.get_ancestry_assignment_display()

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

            self.data['performances'].append(sample_perf_data)


    def build_cohort_metadata(self) -> None:
        cohorts_names = set()
        cohorts_data = []
        for t_sample in self.dataset.samples_training.all():
            cohorts = t_sample.cohorts.all().order_by('name_short')
            for cohort in cohorts:
                if cohort.name_short not in cohorts_names:
                    cohorts_data.append(self.get_data_attr(cohort,'Cohort'))
                    cohorts_names.add(cohort.name_short)
        for v_sample in self.dataset.samples_validation.all():
            cohorts = v_sample.cohorts.all().order_by('name_short')
            for cohort in cohorts:
                if cohort.name_short not in cohorts_names:
                    cohorts_data.append(self.get_data_attr(cohort,'Cohort'))
                    cohorts_names.add(cohort.name_short)
        self.data['cohorts'] = cohorts_data


    def add_dataset_file_urls(self):
        files_ids_dict = self.dataset.files_ids
        found_file_export = []

        # Add file urls to the dataset
        for file in files_ids_dict.keys():
            file_export_key = f'file_url_{file}'
            found_file_export.append(file_export_key)
            self.data['dataset'][file_export_key] = f'{self.file_url_prefix}{files_ids_dict[file]}'
        # Add missing files tags to the dictionnary
        for dataset_file_key in dataset_files:
            if dataset_file_key not in found_file_export:
                self.data['dataset'][dataset_file_key] = None


    def fetch_phi_values_from_sqlite(self) -> None:
        print("  > Fetch SQLite 'phi' values")
        try:
            con = sqlite3.connect(f'{self.sqlite_dir}/{self.sqlite_file}')
            cur = con.cursor()
            cur.execute("SELECT gene, phi FROM extra ORDER BY gene")
            data_table = cur.fetchall()
            cur.close()
            con.close()
            for row in data_table:
                self.phi_values[row[0]] = row[1]
        except:
            print("  > No 'phi' values in SQLite file!")
        self.phi_values_keys = self.phi_values.keys()


    ##############################################################################

    def generate_metadata(self):
        ''' Main method to build the metadata dictionary and then send it to the OPExport class '''
        self.data['dataset'] = self.get_data_attr(self.dataset,'Dataset')
        self.data['publication'] = self.get_data_attr(self.dataset.publication,'Publication')

        # Fetch phi values from the SQLite export
        self.fetch_phi_values_from_sqlite()

        # Add file urls to the dataset
        self.add_dataset_file_urls()

        # Build the cohort metadata
        self.build_cohort_metadata()

        # Prepare score data
        scores = self.dataset.dataset_score.all().order_by('num')
        for score in scores:
            # Build metadata for the Score entry
            self.build_score_metadata(score)

            # Build the performances (metrics, samples, cohorts)
            self.build_performance_metadata(score)

        # Create export
        op_export = OPExport(self.filepath, self.data)
        op_export.generate_sheets()
        op_export.save()