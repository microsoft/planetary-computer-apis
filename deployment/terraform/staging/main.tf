module "resources" {
  source = "../resources"

  environment = "staging"
  region      = "West Europe"

  cluster_cert_issuer = "letsencrypt"
  cluster_cert_server = "https://acme-v02.api.letsencrypt.org/directory"

  pc_test_resources_acr = "pccomponentstest"

  aks_node_count      = 3
  stac_replica_count  = 2
  tiler_replica_count = 2

  # Funcs
  output_storage_account_name    = "pcfilestest"
  output_container_name          = "output"
  funcs_data_api_url             = "https://planetarycomputer.microsoft.com/api/data/v1"
  funcs_tile_request_concurrency = 10

  animation_output_storage_url = "https://pcfilestest.blob.core.windows.net/output/animations"
  image_output_storage_url     = "https://pcfilestest.blob.core.windows.net/output/images"

  prod_log_analytics_workspace_name = "pc-api-loganalytics"
  prod_log_analytics_workspace_id   = "78d48390-b6bb-49a9-b7fd-a86f6522e9c4"
  func_storage_account_url          = "https://pctapisstagingsa.table.core.windows.net/"
  banned_ip_table                   = "blobstoragebannedip"

  sas_node_subnet_name                 = "pct-sas-westeurope-staging-node-subnet"
  sas_node_subnet_virtual_network_name = "pct-sas-westeurope-staging-network"
  sas_node_subnet_resource_group_name  = "pct-sas-westeurope-staging_rg"
}

terraform {
  backend "azurerm" {
    resource_group_name  = "pc-test-manual-resources"
    storage_account_name = "pctesttfstate"
    container_name       = "pc-test-api"
    key                  = "pqe-apis.tfstate"
    use_oidc             = true
    use_azuread_auth     = true
  }
}

output "resources" {
  value     = module.resources
  sensitive = true
}
