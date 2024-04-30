output "environment" {
  value = var.environment
}

output "location" {
  value = local.location
}

output "cluster_name" {
  value = azurerm_kubernetes_cluster.pc.name
}

output "resource_group" {
  value = azurerm_resource_group.pc.name
}

output "tenant_id" {
  value = data.azurerm_client_config.current.tenant_id
}

# -- Postgres

output "pg_host" {
  value = var.pg_host
}

output "pg_port" {
  value = var.pg_port
}

output "pg_user" {
  value = var.pg_user
}

output "pg_database" {
  value = var.pg_database
}

output "pg_password" {
  value     = data.azurerm_key_vault_secret.db_admin_password.value
  sensitive = true
}

# Helm pass-through vars

output "cluster_cert_issuer" {
  value = var.cluster_cert_issuer
}

output "cluster_cert_server" {
  value = var.cluster_cert_server
}

output "cluster_tiler_identity_client_id" {
  value = azurerm_user_assigned_identity.tiler.client_id
}

## Ingress

output "ingress_ip" {
  value = azurerm_public_ip.pc.ip_address
}

output "dns_label" {
  value = azurerm_public_ip.pc.domain_name_label
}

output "secret_provider_keyvault_name" {
  value = var.secret_provider_keyvault_name
}

output "secret_provider_managed_identity_id" {
  value = azurerm_kubernetes_cluster.pc.key_vault_secrets_provider[0].secret_identity[0].client_id
}

output "secret_provider_keyvault_secret" {
  value = var.secret_provider_keyvault_secret
}

## STAC API

output "stac_replica_count" {
  value = var.stac_replica_count
}

## TILER

output "tiler_replica_count" {
  value = var.tiler_replica_count
}

output "pc_sdk_subscription_key" {
  value = data.azurerm_key_vault_secret.pc_sdk_subscription_key.value
}

## Application Insights
output "instrumentation_key" {
  value = azurerm_application_insights.pc_application_insights.instrumentation_key
}

## Storage

output "storage_account_name" {
  value = azurerm_storage_account.pc.name
}

output "storage_account_key" {
  value = azurerm_storage_account.pc.primary_access_key
}

output "collection_config_table_name" {
  value = azurerm_storage_table.collectionconfig.name
}

output "container_config_table_name" {
  value = azurerm_storage_table.containerconfig.name
}

output "ip_exception_config_table_name" {
  value = azurerm_storage_table.ipexceptionlist.name
}

## Redis

output "redis_host" {
  value = azurerm_redis_cache.pc.hostname
}

output "redis_password" {
  value = azurerm_redis_cache.pc.primary_access_key
}

output "redis_port" {
  value = azurerm_redis_cache.pc.ssl_port
}

# Functions

output "function_app_name" {
  value = azurerm_function_app.pcfuncs.name
}
