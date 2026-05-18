# OmicsPred PheWAS import steps

## Pre-processing
1. Update config file `scripts/config.py`
2. Build the EFO database:
```bash
python manage.py runscript phewas.create_efo_db
```

## Data import
Run `imports/scripts/phewas/import_phewas.py`

```bash
python manage.py runscript phewas.import_phewas
```

## Post-processing

1. phewas/add_category.py
2. phewas/get_scorephewas_ancestry_dist.py (need to update the ScorePheWAS queryset beforehand)
