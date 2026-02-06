# OmicsPred import steps

## Data import

1. Update config file `scripts/config.py`
2. Run `import_metadata.py`

```bash
python manage.py runscript import_metadata
```

## Post-processing

1. metadata_post_proccessing.py
2. get_score_ancestry_dist.py
3. update_ensembl_genes.py
4. update_ensembl_proteins.py
5. download_reactome_data.py (optional - only for updated dataset from Reactome)
6. get_reactome_mappings.py
