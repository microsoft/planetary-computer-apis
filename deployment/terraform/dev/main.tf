variable "username" {
  type = string
}

variable "cluster_cert_issuer" {
  type    = string
  default = "letsencrypt-staging"
}

variable "cluster_cert_server" {
  type    = string
  default = "https://acme-staging-v02.api.letsencrypt.org/directory"
}

module "resources" {
  source = "../resources"

  environment = var.username
  region      = "West Europe"

  db_storage_mb = 5120

  cluster_cert_issuer = "letsencrypt"
  cluster_cert_server = "https://acme-v02.api.letsencrypt.org/directory"

  aks_node_count    = 2
  mqe_replica_count = 1
  dqe_replica_count = 1
  sas_replica_count = 1

  sas_expiry_within_datacenter          = 60
  sas_expiry_out_of_datacenter          = 10
  sas_expiry_auth_within_datacenter     = 60 * 24 * 7
  sas_expiry_auth_out_of_datacenter = 60 * 24

  # A Cosmos DB instance that holds full item JSON.
  # The database holds one container per collection,
  # named with the collection ID.
  cosmos_url = "https://pc-cosmostac-east.documents.azure.com:443/"
  cosmos_db_name = "stac"
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
