import os
import pandas as pd
from django.test import TestCase
from django.db.models import Q
from omicspred.models import *
from exports.metadata_build_export import MetadataExport
from exports.tests.config import metadata_exports_dir, sqlite_exports_dir, dataset_selection


class ExportMetadataTest(TestCase):
    """ Test the metadata export script """

    # Load data in DB - from the rest_api/fixtures/ directory
    fixtures = ['db_test']
    databases = {'default'}
    filename = 'OPD000001_DS1_metadata.xlsx'

    spreadsheets = ['Publication','Dataset','Scores','Performances','Cohorts']

    current_dir = os.getcwd()
    output_export_dir = metadata_exports_dir
    data_export_dir = current_dir+'/exports/tests/data/OPD000001'
    output_filepath = f'{output_export_dir}/{filename}'
    # Remove output metadata file before creating it again
    if os.path.isdir(output_export_dir):
        if os.path.isfile(output_filepath):
            try:
                os.remove(output_filepath)
            except OSError:
                print (f'Deletion of the existing output metatada file prior to it\'s regeneration failed ({output_filepath}).')
                exit()

    # Create directory if it doesn't exist
    if not os.path.isdir(output_export_dir):
        try:
            os.mkdir(output_export_dir, 0o755)
        except OSError:
            print (f'Creation of the directory {output_export_dir} failed')
            exit()


    def check_file(self):
        ''' Check file exists and is not empty '''
        print(f' - Check file {self.filename}')
        # Test dir exist
        self.assertEqual(os.path.exists(self.output_export_dir),1)
        # Test file exist
        self.assertEqual(os.path.isfile(self.output_filepath),1)
        # Test file is not null
        test_xls_filesize = os.path.getsize(self.output_filepath)
        self.assertGreater(test_xls_filesize,0)


    def check_spreadsheets(self):
        ''' Check file spreadsheets '''
        print(f' - Check content of {self.filename}')
        ref_filepath = f'{self.data_export_dir}/{self.filename}'
        for sp_name in self.spreadsheets:
            print(f'   > Check spreadsheet {sp_name}')
            df_test = pd.read_excel(self.output_filepath, sheet_name=sp_name, index_col=0)
            df_ref = pd.read_excel(ref_filepath, sheet_name=sp_name, index_col=0)
            # Columns
            self.assertEqual(len(df_test.columns),len(df_ref.columns))
            # Rows
            self.assertEqual(len(df_test.index), len(df_ref.index))


    def test_metadata_export(self):
        print("# Test Metadata export")

        # Mimic DatasetsSelection
        col = list(dataset_selection.keys())[0]
        value = dataset_selection[col]
        param = Q(**{f'{col}':value})

        datasets = Dataset.objects.filter(param).order_by('num')
        dataset = datasets[0]
        metadata2export = MetadataExport(self.output_export_dir,sqlite_exports_dir, dataset)
        metadata2export.generate_metadata()

        self.check_file()
        self.check_spreadsheets()

