
method_name = 'Bayesian Ridge regression'
internal_label = 'Internal'

protein_platform = {'Olink (NEUR)': [ 'Q9BZZ2','Q8TD46','Q2MKA7','Q6ZMJ2','P41217','Q9HAV5','O75509','P78333','Q16719','P53634','O43155','O15232','P08473','P12644','P15509','P28907','Q14108','Q8N126','O60609','Q16775','Q16288','Q8TDQ1','Q8NBI3','Q96GP6','Q9NR71','Q9H3S3','P30533','P29460','P29459','P25774','Q8IUN9','P56159','P17405','Q9H3U7','O94779','O95185','Q96GW7','P22223','P15311','P52798','Q08345','P55285','Q9NP84','Q9HAN9','P21757','Q9ULL4','Q9P0K1','Q6NW40','P16234','P09919','O00214','Q16620','P37023','Q08708','Q92752','P12544','O43157','Q6ISS4','Q01344','P55145','Q92823','Q8NFP4','Q08629','P15151','Q2VWP7','Q9HCK4','Q9UBT3','Q92765','O95727','O75077','Q9BZM5','P48052','Q6UX15','P04216','Q9BS40','Q9Y336','O14594','P14384','P57087','Q96B86','O15197','Q02083','O43561','O14793','Q96LA5','Q96NZ8','P41271','O60462','Q2TAL6','Q9P126']}

studies = {
    'Proteomics_Somalogic': {
        'tissue': {
            'id': 'UBERON_0001969',
            'label': 'blood plasma',
            'description': 'The liquid component of blood, in which erythrocytes are suspended.',
            'url': 'http://purl.obolibrary.org/obo/UBERON_0001969',
            'type': 'tissue'
        },
        'version': '3.0',
        'method_name': method_name,
        'technic': 'aptamer-based multiplex protein assay',
        'internal_cohort': 'INTERVAL',
        'internal_label': internal_label,
        'sample_cohort_info': {
            'INTERVAL': { 'name': 'INTERVAL', 'ancestry': 'European', 'vtype': 'T', 'percent_male': 50.8, 'age': 46.3, 'age_sd': 14.2 },
            'FENLAND':  { 'name': 'FENLAND', 'ancestry': 'European', 'vtype': 'EV', 'percent_male': 47.1, 'age': 48.8, 'age_sd': 7.4 },
            'MEC_CN':   { 'name': 'MEC', 'ancestry': 'East Asian', 'vtype': 'EV', 'percent_male': 46, 'age': 51.9, 'age_sd': 10.9 },
            'MEC_IN':   { 'name': 'MEC', 'ancestry': 'South Asian', 'vtype': 'EV', 'percent_male': 45, 'age': 44, 'age_sd': 12 },
            'MEC_MA':   { 'name': 'MEC', 'ancestry': 'Additional Asian Ancestries', 'vtype': 'EV', 'percent_male': 43.9, 'age': 44.4, 'age_sd': 11.3 },
            'JHS':      { 'name': 'JHS', 'ancestry': 'African American', 'vtype': 'EV', 'percent_male': 39, 'age': 55.7, 'age_sd': 12.8 }
        }
    },
    'Proteomics_Olink': {
        'tissue': {
            'id': 'UBERON_0001969',
            'label': 'blood plasma',
            'description': 'The liquid component of blood, in which erythrocytes are suspended.',
            'url': 'http://purl.obolibrary.org/obo/UBERON_0001969',
            'type': 'tissue'
        },
        'method_name': method_name,
        'full_name': 'Olink Target',
        'technic': 'antibody-based proximity extension assay for proteins',
        'internal_cohort': 'INTERVAL',
        'internal_label': internal_label,
        'sample_cohort_info': {
            'INTERVAL': { 'name': 'INTERVAL', 'ancestry': 'European', 'vtype': 'T', 'percent_male': 59.3, 'age': 59, 'age_sd': 6.7 },
            'NSPHS':    { 'name': 'NSPHS', 'ancestry': 'European', 'vtype': 'EV', 'percent_male': 46.7, 'age': 49.6, 'age_sd': 20.2  },
            'ORCADES':  { 'name': 'ORCADES', 'ancestry': 'European', 'vtype': 'EV', 'percent_male': 44.1, 'age': 53.8, 'age_sd': 15.7  }
        }
    },
    'Metabolomics_Nightingale': {
        'tissue': {
            'id': 'BTO_0000133',
            'label': 'blood serum',
            'description': 'The cell-free portion of the blood from which the fibrinogen has been separated in the process of clotting.',
            'url': 'http://purl.obolibrary.org/obo/BTO_0000133',
            'type': 'tissue'
        },
        'method_name': method_name,
        'technic': 'proton nuclear magnetic resonance (NMR) spectroscopy platform',
        'internal_cohort': 'INTERVAL',
        'internal_label': internal_label,
        'sample_cohort_info': {
            'INTERVAL': { 'name': 'INTERVAL', 'ancestry': 'European', 'vtype': 'T', 'percent_male': 51, 'age': 43.7, 'age_sd': 14.1 },
            'UKB':      { 'name': 'UKB', 'ancestry': 'European', 'vtype': 'EV', 'percent_male': 45.8, 'age': 56.5, 'age_sd': 8.1 },
            'ORCADES':  { 'name': 'ORCADES', 'ancestry': 'European', 'vtype': 'EV', 'percent_male': 40, 'age': 53.9, 'age_sd': 15 },
            'VIKING':   { 'name': 'VIKING', 'ancestry': 'European', 'vtype': 'EV', 'percent_male': 39.9, 'age': 49.8, 'age_sd': 15.2},
            'MEC_CN':   { 'name': 'MEC', 'ancestry': 'East Asian', 'vtype': 'EV', 'percent_male': 47.2, 'age': 52.1, 'age_sd': 9.9 },
            'MEC_IN':   { 'name': 'MEC', 'ancestry': 'South Asian', 'vtype': 'EV', 'percent_male': 43.7, 'age': 44.5, 'age_sd': 11.6 },
            'MEC_MA':   { 'name': 'MEC', 'ancestry': 'Additional Asian Ancestries', 'vtype': 'EV', 'percent_male': 42.9, 'age': 44.9, 'age_sd': 11.1 }
        }
    },
    'Metabolomics_Metabolon': {
        'tissue': {
            'id': 'UBERON_0001969',
            'label': 'blood plasma',
            'description': 'The liquid component of blood, in which erythrocytes are suspended.',
            'url': 'http://purl.obolibrary.org/obo/UBERON_0001969',
            'type': 'tissue'
        },
        'method_name': method_name,
        'full_name': 'Metabolon HD4',
        'technic': 'untargeted mass spectrometry metabolomics platform',
        'internal_cohort': 'INTERVAL',
        'internal_label': internal_label,
        'sample_cohort_info': {
            'INTERVAL':              { 'name': 'INTERVAL', 'ancestry': 'European', 'vtype': 'T', 'percent_male': 51, 'age': 43.9, 'age_sd': 14.1 },
            'INTERVAL_Withheld_Set': { 'name': 'INTERVAL withheld subset', 'ancestry': 'European', 'vtype': 'IV', 'percent_male': 49.4, 'age': 47.9, 'age_sd': 13.8 },
            'ORCADES':               { 'name': 'ORCADES', 'ancestry': 'European', 'vtype': 'EV', 'percent_male': 43.9, 'age': 54, 'age_sd': 15.3 }
        }
    },
    'Transcriptomics_Illumina_RNAseq': {
        'tissue': {
            'id': 'UBERON_0000178',
            'label': 'blood',
            'description': 'A fluid that is composed of blood plasma and erythrocytes.',
            'url': 'http://purl.obolibrary.org/obo/UBERON_0000178',
            'type': 'tissue'
        },
        'method_name': method_name,
        'full_name': 'Illumina NovaSeq 6000',
        'internal_cohort': 'INTERVAL',
        'internal_label': internal_label,
        'sample_cohort_info': {
            'INTERVAL':              { 'name': 'INTERVAL', 'ancestry': 'European', 'vtype': 'T', 'percent_male': 56.4, 'age': 54.6, 'age_sd': 11.6 },
            'INTERVAL_Withheld_Set': { 'name': 'INTERVAL withheld subset', 'ancestry': 'European', 'vtype': 'IV', 'percent_male': 49.5, 'age': 45, 'age_sd': 13.1 },
        }
    }
}
