import os
import sqlite3
import tempfile
from django.test import TestCase
from omicspred.models import *
from exports.sqlite_export import SqliteExport
from exports.tests.config import sqlite_default_values


class ExportSQLiteTest(TestCase):
    """ Test the metadata export script """

    # Load data in DB - from the rest_api/fixtures/ directory
    fixtures = ['db_test']
    databases = {'default'}

    opp_id = 'OPP000001'
    opd_id = 'OPD000001'
    dataset_label = 'DS1'
    current_dir = os.getcwd()
    scoring_files_dir = sqlite_default_values['scoring_files_dir']
    use_different_id_as_gene = sqlite_default_values['use_different_id_as_gene']
    
    sqlite_filename = f'{opd_id}_{dataset_label}.db'

    # SQLite ref
    ref_sqlite_dir = current_dir+'/exports/tests/data/'+opd_id
    ref_sqlite_filepath = f'{ref_sqlite_dir}/{sqlite_filename}'
    # SQLite Output
    output_sqlite_dir = sqlite_default_values['sqlite_dir']
    output_sqlite_filepath = f'{output_sqlite_dir}{sqlite_filename}'

    # Remove output SQLite file before creating it again
    if os.path.isdir(output_sqlite_dir):
        if os.path.isfile(output_sqlite_filepath):
            try:
                os.remove(output_sqlite_filepath)
            except OSError:
                print (f'Deletion of the existing output SQLite file prior to it\'s regeneration failed ({output_filepath}).')
                exit()
    # Create directory if it doesn't exist
    if not os.path.isdir(output_sqlite_dir):
        try:
            os.mkdir(output_sqlite_dir, 0o755)
        except OSError:
            print (f'Creation of the directory {output_sqlite_dir} failed')
            exit()


    def get_one_row_data(self,cursor:sqlite3.Cursor,table_name:str) -> tuple:
        r_cursor = cursor.execute(f"SELECT * FROM {table_name};")
        return r_cursor.fetchone()


    def get_weights_data(self,cursor:sqlite3.Cursor) -> list:
        w_cursor = cursor.execute(f"SELECT * FROM weights;")
        return w_cursor.fetchall()


    def get_extra_data(self,cursor:sqlite3.Cursor):
        return self.get_one_row_data(cursor,'extra')


    def get_sample_info_data(self,cursor:sqlite3.Cursor):
        return self.get_one_row_data(cursor,'sample_info')


    def get_genome_build_data(self,cursor:sqlite3.Cursor):
        return self.get_one_row_data(cursor,'genome_build')


    def get_table_names(self,cursor:sqlite3.Cursor):
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        return [row[0] for row in cursor.fetchall()]


    def get_table_schema(self,cursor:sqlite3.Cursor, table_name:str):
        cursor.execute(f"PRAGMA table_info({table_name});")
        return cursor.fetchall()


    def get_table_row_count(self,cursor:sqlite3.Cursor, table_name:str):
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        return cursor.fetchone()[0]


    def test_sqlite_export(self):
        print("\n## Test SQLite export ##")
        print("> Test SQLite export")
        datasets = Dataset.objects.filter(id=self.opd_id)
        sqlite_export = SqliteExport(self.opp_id,self.output_sqlite_dir,self.scoring_files_dir,datasets,self.use_different_id_as_gene)
        sqlite_export.generate_sqlite_files(True)

        sqlite_ref_connection = sqlite3.connect(self.ref_sqlite_filepath)
        sqlite_ref_cursor = sqlite_ref_connection.cursor()
        ref_extra = self.get_extra_data(sqlite_ref_cursor)
        ref_weights = self.get_weights_data(sqlite_ref_cursor)
        ref_sample_info = self.get_sample_info_data(sqlite_ref_cursor)
        ref_genome_build = self.get_genome_build_data(sqlite_ref_cursor)
        sqlite_ref_cursor.close()
        sqlite_ref_connection.close()

        sqlite_output_connection = sqlite3.connect(self.output_sqlite_filepath)
        sqlite_output_cursor = sqlite_output_connection.cursor()
        output_extra = self.get_extra_data(sqlite_output_cursor)
        output_weights = self.get_weights_data(sqlite_output_cursor)
        output_sample_info = self.get_sample_info_data(sqlite_output_cursor)
        output_genome_build = self.get_genome_build_data(sqlite_output_cursor)
        sqlite_output_cursor.close()
        sqlite_output_connection.close()

        # Test content of the `extra` table
        for index, col_value in enumerate(output_extra):
            self.assertEqual(output_extra[index],ref_extra[index])

        # Test content of the `weights` table
        self.assertEqual(len(output_weights),len(ref_weights))
        for index, col_value in enumerate(output_weights[1]):
            self.assertEqual(output_weights[1][index],ref_weights[1][index])

        # Test content of the `sample_info` table
        for index, col_value in enumerate(output_sample_info):
            self.assertEqual(output_sample_info[index],ref_sample_info[index])

        # Test content of the `genome_build` table
        for index, col_value in enumerate(output_genome_build):
            self.assertEqual(output_genome_build[index],ref_genome_build[index])


    def test_sqlite_export_has_expected_tables(self):
        print("> Test SQLite export tables")
        datasets = Dataset.objects.filter(id=self.opd_id)
        sqlite_export = SqliteExport(self.opp_id,self.output_sqlite_dir,self.scoring_files_dir,datasets,self.use_different_id_as_gene)
        sqlite_export.generate_sqlite_files(True)

        sqlite_output_connection = sqlite3.connect(self.output_sqlite_filepath)
        sqlite_output_cursor = sqlite_output_connection.cursor()
        table_names = self.get_table_names(sqlite_output_cursor)
        sqlite_output_cursor.close()
        sqlite_output_connection.close()

        self.assertTrue({'extra', 'weights', 'sample_info', 'genome_build'}.issubset(set(table_names)))


    def test_sqlite_export_has_expected_schema(self):
        print("> Test SQLite export schema")
        datasets = Dataset.objects.filter(id=self.opd_id)
        sqlite_export = SqliteExport(self.opp_id,self.output_sqlite_dir,self.scoring_files_dir,datasets,self.use_different_id_as_gene)
        sqlite_export.generate_sqlite_files(skip_zip=True)

        sqlite_output_connection = sqlite3.connect(self.output_sqlite_filepath)
        sqlite_output_cursor = sqlite_output_connection.cursor()

        schema_weights = self.get_table_schema(sqlite_output_cursor, 'weights')
        schema_extra = self.get_table_schema(sqlite_output_cursor, 'extra')

        sqlite_output_cursor.close()
        sqlite_output_connection.close()

        self.assertGreater(len(schema_weights), 0)
        self.assertGreater(len(schema_extra), 0)
        self.assertIn('gene', [col[1] for col in schema_weights])
        self.assertIn('rsid', [col[1] for col in schema_weights])
        self.assertIn('genename', [col[1] for col in schema_extra])


    def test_sqlite_export_has_expected_row_counts(self):
        print("> Test SQLite export row counts")
        datasets = Dataset.objects.filter(id=self.opd_id)
        sqlite_export = SqliteExport(self.opp_id,self.output_sqlite_dir,self.scoring_files_dir,datasets,self.use_different_id_as_gene)
        sqlite_export.generate_sqlite_files(skip_zip=True)

        sqlite_output_connection = sqlite3.connect(self.output_sqlite_filepath)
        sqlite_output_cursor = sqlite_output_connection.cursor()

        weights_count = self.get_table_row_count(sqlite_output_cursor, 'weights')
        sample_info_count = self.get_table_row_count(sqlite_output_cursor, 'sample_info')

        sqlite_output_cursor.close()
        sqlite_output_connection.close()

        self.assertGreater(weights_count, 0)
        self.assertEqual(sample_info_count, 1)

    def test_sqlite_export_with_opgs_id_as_gene(self):
        print("> Test SQLite export with opgs_id as gene")
        datasets = Dataset.objects.filter(id=self.opd_id)
        sqlite_export = SqliteExport(
            self.opp_id,
            self.output_sqlite_dir,
            self.scoring_files_dir,
            datasets,
            'opgs_id'
        )
        sqlite_export.generate_sqlite_files(skip_zip=True)

        sqlite_output_connection = sqlite3.connect(self.output_sqlite_filepath)
        sqlite_output_cursor = sqlite_output_connection.cursor()

        schema_weights = self.get_table_schema(sqlite_output_cursor, 'weights')
        schema_extra = self.get_table_schema(sqlite_output_cursor, 'extra')

        sqlite_output_cursor.close()
        sqlite_output_connection.close()

        weights_columns = [col[1] for col in schema_weights]
        extra_columns = [col[1] for col in schema_extra]

        self.assertIn('gene', weights_columns)
        self.assertNotIn('omicspred_id', weights_columns)
        self.assertIn('genename', extra_columns)


    def test_sqlite_export_matches_reference_row_counts(self):
        print("> Test SQLite export matches reference row counts")
        datasets = Dataset.objects.filter(id=self.opd_id)
        sqlite_export = SqliteExport(
            self.opp_id,
            self.output_sqlite_dir,
            self.scoring_files_dir,
            datasets,
            self.use_different_id_as_gene
        )
        sqlite_export.generate_sqlite_files(skip_zip=True)

        sqlite_ref_connection = sqlite3.connect(self.ref_sqlite_filepath)
        sqlite_ref_cursor = sqlite_ref_connection.cursor()
        sqlite_output_connection = sqlite3.connect(self.output_sqlite_filepath)
        sqlite_output_cursor = sqlite_output_connection.cursor()

        ref_counts = {
            'weights': self.get_table_row_count(sqlite_ref_cursor, 'weights'),
            'sample_info': self.get_table_row_count(sqlite_ref_cursor, 'sample_info'),
            'genome_build': self.get_table_row_count(sqlite_ref_cursor, 'genome_build'),
            'extra': self.get_table_row_count(sqlite_ref_cursor, 'extra'),
        }
        output_counts = {
            'weights': self.get_table_row_count(sqlite_output_cursor, 'weights'),
            'sample_info': self.get_table_row_count(sqlite_output_cursor, 'sample_info'),
            'genome_build': self.get_table_row_count(sqlite_output_cursor, 'genome_build'),
            'extra': self.get_table_row_count(sqlite_output_cursor, 'extra'),
        }

        sqlite_ref_cursor.close()
        sqlite_ref_connection.close()
        sqlite_output_cursor.close()
        sqlite_output_connection.close()

        self.assertEqual(output_counts, ref_counts)


    def setUp(self):
        print("> Test setup")
        super().setUp()
        self.temp_dir = tempfile.mkdtemp()
        self.output_sqlite_dir = f"{self.temp_dir}/"
        self.output_sqlite_filepath = f"{self.output_sqlite_dir}{self.sqlite_filename}"


    def test_sqlite_export_skip_zip_keeps_db_file(self):
        print("> Test SQLite export skip zip keeps db file")
        datasets = Dataset.objects.filter(id=self.opd_id)
        sqlite_export = SqliteExport(
            self.opp_id,
            self.output_sqlite_dir,
            self.scoring_files_dir,
            datasets,
            self.use_different_id_as_gene,
        )
        sqlite_export.generate_sqlite_files(skip_zip=True)

        self.assertTrue(os.path.exists(self.output_sqlite_filepath))
        self.assertFalse(os.path.exists(f"{self.output_sqlite_filepath}.gz"))


    def test_sample_info_matches_sum_of_training_samples(self):
        print("> Test sample_info matches sum of training samples")
        dataset = Dataset.objects.get(id=self.opd_id)
        expected = sum(s.sample_number for s in dataset.samples_training.all())

        sqlite_export = SqliteExport(
            self.opp_id,
            self.output_sqlite_dir,
            self.scoring_files_dir,
            [dataset],
            self.use_different_id_as_gene,
        )
        sqlite_export.generate_sqlite_files(skip_zip=True)

        conn = sqlite3.connect(self.output_sqlite_filepath)
        row = conn.execute("SELECT COUNT(*) FROM sample_info").fetchone()
        self.assertEqual(row[0], 1)

        sample_count = conn.execute("SELECT * FROM sample_info").fetchone()[0]
        self.assertEqual(sample_count, expected)
        conn.close()