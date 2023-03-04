module "resources" {
  source = "../resources"

  environment = "staging"
  region      = "West Europe"

  k8s_version = "1.25.5"

  cluster_cert_issuer = "letsencrypt"
  cluster_cert_server = "https://acme-v02.api.letsencrypt.org/directory"

  aks_node_count      = 2
  stac_replica_count  = 2
  tiler_replica_count = 2

  # Funcs
  output_storage_account_name    = "pcfilestest"
  output_container_name          = "output"
  funcs_data_api_url             = "https://planetarycomputer.microsoft.com/api/data/v1"
  funcs_tile_request_concurrency = 10

  animation_output_storage_url = "https://pcfilestest.blob.core.windows.net/output/animations"
  image_output_storage_url     = "https://pcfilestest.blob.core.windows.net/output/images"

}

terraform {
  backend "azurerm" {
    resource_group_name  = "pc-test-manual-resources"
    storage_account_name = "pctesttfstate"
    container_name       = "pc-test-api"
    key                  = "pqe-apis.tfstate"
  }
}

output "resources" {
  value     = module.resources
  sensitive = true
}
