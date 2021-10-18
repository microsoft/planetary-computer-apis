variable "environment" {
  type = string
}

variable "region" {
  type = string
}

variable "aks_node_count" {
  type = number
}

variable "cluster_cert_issuer" {
  type = string
  validation {
    condition     = can(regex("^(letsencrypt|letsencrypt-staging)$", var.cluster_cert_issuer))
    error_message = "Must be letsencrypt or letsencrypt-staging."
  }

}

variable "cluster_cert_server" {
  type = string
}

variable "mqe_replica_count" {
  type = number
}

variable "dqe_replica_count" {
  type = number
}

# -- Postgres

variable "pg_host" {
  type = string
  default = "pct-stacdb.postgres.database.azure.com"
}

variable "pg_port" {
  type = string
  default = "5432"
}

variable "pg_user" {
  type = string
  default ="planetarycomputertest"
}

variable "pg_database" {
  type = string
  default = "postgres"
}

variable "pg_password_secret_name" {
  type = string
  description = "The secret name in the KeyVault that holds the db password"
  default = "pct-db-password"
}

# -----------------
# Attach ACR
# Defaults to common resources in Planetary Computer Test

variable "pc_test_resources_rg" {
  type    = string
  default = "pc-test-manual-resources"
}

variable "pc_test_resources_kv" {
  type    = string
  default = "pc-test-deploy-secrets"
}

variable "pc_test_resources_acr" {
  type    = string
  default = "pccomponentstest"
}

# -----------------
# Local variables

locals {
  stack_id              = "pct-pqe"
  location              = lower(replace(var.region, " ", ""))
  prefix                = "${local.stack_id}-${local.location}-${var.environment}"
  deploy_secrets_prefix = "${local.stack_id}-${var.environment}"
  pqe_dns               = "${local.stack_id}-${var.environment}.${local.location}.cloudapp.azure.com"

}
