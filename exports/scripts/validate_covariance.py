from exports.datasets import DatasetsSelection
from exports.covariance_validation import CovarianceValidation


# covariance_dir = '/Users/lg10/Workspace/datafiles/OmicsPred/PCAIR/covariances'
# sqlite_dir = '/Users/lg10/Workspace/datafiles/OmicsPred/PCAIR/sqlite_exports'
# var_type = 'rsid'

# covariance_dir = '/Users/lg10/Workspace/datafiles/OmicsPred/GTEx_V8/covariances/MASHR_eQTL'
# sqlite_dir = '/Users/lg10/Workspace/datafiles/OmicsPred/GTEx_V8/sqlite_exports_tmp_eQTL_MASHR'
# var_type = 'VarID'

covariance_dir = '/Users/lg10/Workspace/datafiles/OmicsPred/GTEx_V8/covariances/MASHR_sQTL'
sqlite_dir = '/Users/lg10/Workspace/datafiles/OmicsPred/GTEx_V8/sqlite_exports_tmp_sQTL_MASHR'
var_type = 'VarID'

def run():
    ds_selection = DatasetsSelection()
    datasets = ds_selection.get_datasets()

    print("## Start Covariance Validation, dataset by dataset")
    covariance_validation = CovarianceValidation(covariance_dir,sqlite_dir,datasets,var_type)
    covariance_validation.validate_covariance_files()