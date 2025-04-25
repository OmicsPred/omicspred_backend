import logging


logger = logging.getLogger(__name__)

class GenericData():

    # Non ascii symbols (unicode notation)
    non_ascii_chars = {
        '\u2009': ' ', # Thin Space
        '\u2013': '-', # En dash
        '\u2014': '-', # Em dash
        '\u2022': '-', # Bullet
        '\u2019': "'", # Right single quotation mark
        '\u201A': '',  # Single low-9 quotation mark,
        '\uFEFF': ''   # byte order mark (BOM)
    }

    # Applications DB 
    applications_db = 'applications'

    def __init__(self):
        self.model = None
        self.data = {}
        self.additional_data = {}
        # self.report = {'error': {}, 'warning': {}, 'import': {} }
        # self.report_types = self.report.keys()

    def add_data(self, field, value):
        ''' Insert new data into the 'data' dictionary. '''
        if type(value) == str:
            value = value.strip()
            # Remove/replace some of the non-ascii characters
            for char in self.non_ascii_chars.keys():
                if char in value:
                    logger.warning(f'Found non ascii character "{char}" for "{field}": "{value}"')
                    # self.parsing_report_warning(f'Found non ascii character "{char}" for "{field}": "{value}"')
                    value = value.replace(char, self.non_ascii_chars[char])
        self.data[field] = value


    def add_other_model(self,data_model_type:str,data_content:object):
        self.additional_data[data_model_type] = data_content


    def generate_generic_model(self, model):
        unsaved_model = model()
        # unsaved_model.set_score_ids(self.next_id_number(Score, 'num'))
        for field, val in self.data.items():
            setattr(unsaved_model, field, val)
        return unsaved_model


    def next_id_number(self, model, field):
        ''' Fetch the new primary key value. '''
        assigned = 1
        if len(model.objects.all()) != 0:
            assigned = model.objects.latest(field).pk + 1
            # assigned = model.objects.all().order_by(field).last() + 1
        return assigned