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

  k8s_version = "1.22.4"

  cluster_cert_issuer = "letsencrypt"
  cluster_cert_server = "https://acme-v02.api.letsencrypt.org/directory"

  aks_node_count    = 1
  stac_replica_count = 1
  tiler_replica_count = 1

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
