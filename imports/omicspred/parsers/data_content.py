
method_name = 'Bayesian Ridge regression'
internal_label = 'Internal'

protein_platform = {'Olink (NEUR)': [ 'Q9BZZ2','Q8TD46','Q2MKA7','Q6ZMJ2','P41217','Q9HAV5','O75509','P78333','Q16719','P53634','O43155','O15232','P08473','P12644','P15509','P28907','Q14108','Q8N126','O60609','Q16775','Q16288','Q8TDQ1','Q8NBI3','Q96GP6','Q9NR71','Q9H3S3','P30533','P29460','P29459','P25774','Q8IUN9','P56159','P17405','Q9H3U7','O94779','O95185','Q96GW7','P22223','P15311','P52798','Q08345','P55285','Q9NP84','Q9HAN9','P21757','Q9ULL4','Q9P0K1','Q6NW40','P16234','P09919','O00214','Q16620','P37023','Q08708','Q92752','P12544','O43157','Q6ISS4','Q01344','P55145','Q92823','Q8NFP4','Q08629','P15151','Q2VWP7','Q9HCK4','Q9UBT3','Q92765','O95727','O75077','Q9BZM5','P48052','Q6UX15','P04216','Q9BS40','Q9Y336','O14594','P14384','P57087','Q96B86','O15197','Q02083','O43561','O14793','Q96LA5','Q96NZ8','P41271','O60462','Q2TAL6','Q9P126']}

studies = {
    'Proteomics_Olink/UKB_EUR': {
        'tissue': {
            'id': 'UBERON_0001969',
            'label': 'blood plasma',
            'description': 'The liquid component of blood, in which erythrocytes are suspended.',
            'url': 'http://purl.obolibrary.org/obo/UBERON_0001969',
            'type': 'tissue'
        },
        'method_name': method_name,
        'full_name': 'Olink',
        'version': 'Explore',
        'technique': 'antibody-based proximity extension assay for proteins',
        'dataset_name': 'UKB European',
        'internal_cohort': 'UKB',
        'internal_label': internal_label,
        'sample_cohort_info': {
            'UKB':                { 'name': 'UKB', 'name_full': 'UK Biobank', 'ancestry': 'European', 'vtype': 'T', 'participants': 34557 },
            'UKB_Withheld_ALL':   { 'name': 'UKB_Withheld', 'name_full': 'UK Biobank Withheld Set', 'ancestry': 'European,Ad Mixed American,African,East Asian,South Asian', 'vtype': 'IV',  'participants': 17758 },
            'UKB_Withheld_EUR':   { 'name': 'UKB_Withheld', 'name_full': 'UK Biobank Withheld Set', 'ancestry': 'European', 'vtype': 'IV', 'participants': 14322 },
            'UKB_Withheld_AMR':   { 'name': 'UKB_Withheld', 'name_full': 'UK Biobank Withheld Set', 'ancestry': 'Ad Mixed American', 'vtype': 'IV', 'participants': 81 },
            'UKB_Withheld_AFR':   { 'name': 'UKB_Withheld', 'name_full': 'UK Biobank Withheld Set', 'ancestry': 'African', 'vtype': 'IV', 'participants': 1290 },
            'UKB_Withheld_EAS':   { 'name': 'UKB_Withheld', 'name_full': 'UK Biobank Withheld Set', 'ancestry': 'East Asian', 'vtype': 'IV', 'participants': 224 },
            'UKB_Withheld_SAS':   { 'name': 'UKB_Withheld', 'name_full': 'UK Biobank Withheld Set', 'ancestry': 'South Asian', 'vtype': 'IV', 'participants': 1013 },
            'INTERVAL':           { 'name': 'INTERVAL', 'name_full': 'INTERVAL', 'ancestry': 'European', 'vtype': 'EV', 'participants': 4800 }
        },
        'species': 9606
    },
    'Proteomics_Olink/UKB_MULTI': {
        'tissue': {
            'id': 'UBERON_0001969',
            'label': 'blood plasma',
            'description': 'The liquid component of blood, in which erythrocytes are suspended.',
            'url': 'http://purl.obolibrary.org/obo/UBERON_0001969',
            'type': 'tissue'
        },
        'method_name': method_name,
        'full_name': 'Olink',
        'version': 'Explore',
        'technique': 'antibody-based proximity extension assay for proteins',
        'dataset_name': 'UKB Multi-ancestry',
        'internal_cohort': 'UKB',
        'internal_label': internal_label,
        'sample_cohort_info': {
            'UKB':          { 'name': 'UKB', 'name_full': 'UK Biobank', 'ancestry': 'Multi-ancestry', 'vtype': 'T', 'participants': 52315 },
            'INTERVAL':     { 'name': 'INTERVAL', 'name_full': 'INTERVAL', 'ancestry': 'European', 'vtype': 'EV', 'participants': 4800 }
        },
        'species': 9606
    }
}
