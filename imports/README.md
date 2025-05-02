# OmicsPred import steps:

## Data import
Run `import_metadata.py`

```
python manage.py runscript import_metadata
```

## Post-processing
1. get_score_ancestry_dist.py
2. update_ensembl_genes.py
3. update_ensembl_proteins.py
4. download_reactome_data.py
5. get_reactome_mappings.py