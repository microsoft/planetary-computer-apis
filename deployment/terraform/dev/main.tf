variable "username" {
  type = string
}

module "resources" {
  source = "../resources"

  environment = var.username
  region      = "West Europe"

  k8s_version = "1.22.4"

  cluster_cert_issuer = "letsencrypt"
  cluster_cert_server = "https://acme-v02.api.letsencrypt.org/directory"

  aks_node_count    = 1
  stac_replica_count = 1
  tiler_replica_count = 1

  # Funcs
  output_storage_account_name = "pcfilestest"
  output_container_name = "output"
  funcs_data_api_url = "https://planetarycomputer.microsoft.com/api/data/v1"
  funcs_tile_request_concurrency = 10

  animation_output_storage_url = "https://pcfilestest.blob.core.windows.net/output/animations"
  image_output_storage_url = "https://pcfilestest.blob.core.windows.net/output/images"

}

terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}

output "resources" {
  value     = module.resources
  sensitive = true
}
