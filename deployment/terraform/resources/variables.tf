variable "environment" {
  type = string
}

variable "region" {
  type = string
}

variable "pc_test_resources_rg" {
  type    = string
  default = "pc-test-manual-resources"
}

variable "pc_resources_rg" {
  type    = string
  default = "pc-manual-resources"
}

variable "pc_test_resources_kv" {
  type    = string
  default = "pc-test-deploy-secrets"
}

variable "pc_test_resources_acr" {
  type    = string
  default = "pccomponentstest"
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

variable "stac_replica_count" {
  type = number
}

variable "tiler_replica_count" {
  type = number
}

# -- Postgres

variable "pg_host" {
  type    = string
  default = "pct-stacdb.postgres.database.azure.com"
}

variable "pg_port" {
  type    = string
  default = "5432"
}

variable "pg_user" {
  type    = string
  default = "planetarycomputertest"
}

variable "pg_database" {
  type    = string
  default = "postgres"
}

variable "pg_password_secret_name" {
  type        = string
  description = "The secret name in the KeyVault that holds the db password"
  default     = "pct-db-password"
}

variable "pc_sdk_subscription_key_secret_name" {
  type        = string
  description = "The secret name in the KeyVault that holds the PC subscription key used by the tiler"
  default     = "pct-tiler-sdk-subscription-key"
}

variable "secret_provider_keyvault_name" {
  type        = string
  description = "The name of the KeyVault that holds the secrets"
  default     = "pc-deploy-secrets"
}

variable "secret_provider_keyvault_secret" {
  type        = string
  description = "The name of the certificate in the KeyVault for TLS ingress"
  default     = "planetarycomputer-test-certificate"
}

# -- Functions --

variable "output_storage_account_name" {
  type = string
}

variable "output_container_name" {
  type = string
}

variable "funcs_tile_request_concurrency" {
  type    = number
  default = 10
}

variable "funcs_data_api_url" {
  type = string
}

# Animation

variable "animation_output_storage_url" {
  type = string
}

# Image

variable "image_output_storage_url" {
  type = string
}

variable "prod_log_analytics_workspace_name" {
  type = string
}

# -----------------
# Local variables

locals {
  stack_id      = "pct-apis"
  location      = lower(replace(var.region, " ", ""))
  prefix        = "${local.stack_id}-${local.location}-${var.environment}"
  nodash_prefix = replace("${local.stack_id}${var.environment}", "-", "")
}
