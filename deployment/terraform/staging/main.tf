module "resources" {
  source = "../resources"

  environment = "staging"
  region = "West Europe"

  k8s_version = "1.20.7"

  cluster_cert_issuer = "letsencrypt"
  cluster_cert_server = "https://acme-v02.api.letsencrypt.org/directory"

  aks_node_count = 2
  stac_replica_count = 2
  tiler_replica_count = 2

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
  value = module.resources
  sensitive = true
}