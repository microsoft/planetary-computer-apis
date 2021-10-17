module "resources" {
  source = "../resources"

  environment = "staging"
  region = "West Europe"

  # A very specific but random number that was set
  # while trying to debug why the staging database
  # went down
  db_storage_mb = 297984

  cluster_cert_issuer = "letsencrypt"
  cluster_cert_server = "https://acme-v02.api.letsencrypt.org/directory"

  aks_node_count = 6
  mqe_replica_count = 2
  dqe_replica_count = 2
  sas_replica_count = 1

  sas_expiry_within_datacenter = 60
  sas_expiry_out_of_datacenter = 10
  sas_expiry_auth_within_datacenter = 60 * 24 * 7
  sas_expiry_auth_out_of_datacenter = 60 * 24

  cosmos_url = "https://pc-cosmostac-east.documents.azure.com:443/"
  cosmos_db_name = "stac"
}

terraform {
  backend "azurerm" {
    resource_group_name  = "pc-test-manual-resources"
    storage_account_name = "pctesttfstate"
    container_name       = "metadata-query-api"
    key                  = "staging.terraform.tfstate"
  }
}

output "resources" {
  value = module.resources
  sensitive = true
}